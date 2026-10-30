from __future__ import annotations

import json
import math
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/river-shift", tags=["RiverShift"])

ASF_SEARCH_URL = "https://api.daac.asf.alaska.edu/services/search/param"
MAX_RESULTS = 200
MAX_AOI_AREA_KM2 = 1_000.0
TIMEOUT_SECONDS = 25
EARTH_RADIUS_METERS = 6_371_000.0

Maturity = Literal["BETA", "PROVISIONAL", "ALL"]
Polarization = Literal["HH", "HH+HV", "HH+VV", "HH+HV+VH+VV", "VV", "VV+VH", "LH+LV", "RH+RV"]
FlightDirection = Literal["ASCENDING", "DESCENDING"]


class RiverShiftCatalogRequest(BaseModel):
    coordinates: list[list[float]] = Field(min_length=4, max_length=400)
    start_date: date
    end_date: date
    maturity: Maturity = "PROVISIONAL"
    main_band_polarization: Polarization | None = None
    flight_direction: FlightDirection | None = None
    max_results: int = Field(default=100, ge=1, le=MAX_RESULTS)


class RiverShiftProduct(BaseModel):
    granule_name: str
    product_type: Literal["GCOV"] = "GCOV"
    maturity: Literal["BETA", "PROVISIONAL", "UNKNOWN"]
    download_url: str | None = None
    start_time_utc: str | None = None
    stop_time_utc: str | None = None
    flight_direction: str | None = None
    relative_orbit: str | None = None
    cycle: str | None = None
    frame: str | None = None
    bandwidth_mode: str | None = None
    polarization_code: str | None = None
    main_band_polarization: str | None = None
    size_mb: float | None = None


class RiverShiftCatalogResponse(BaseModel):
    mode: Literal["catalogue_only"] = "catalogue_only"
    mission: Literal["NISAR"] = "NISAR"
    product: Literal["GCOV"] = "GCOV"
    status: Literal["ready", "no_data", "upstream_error"]
    message: str
    data_downloaded: Literal[False] = False
    scientific_analysis_performed: Literal[False] = False
    query: dict[str, Any]
    product_count: int = 0
    products: list[RiverShiftProduct] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def _validate_coordinates(coordinates: list[list[float]]) -> list[tuple[float, float]]:
    if len(coordinates) < 4:
        raise HTTPException(status_code=422, detail="AOI must be a closed polygon with at least 3 vertices.")
    normalized: list[tuple[float, float]] = []
    for point in coordinates:
        if len(point) != 2:
            raise HTTPException(status_code=422, detail="Each coordinate must be [longitude, latitude].")
        lon, lat = point
        if not math.isfinite(lon) or not math.isfinite(lat):
            raise HTTPException(status_code=422, detail="AOI coordinates must be finite numbers.")
        if not -180 <= lon <= 180 or not -90 <= lat <= 90:
            raise HTTPException(status_code=422, detail="AOI coordinates must use WGS84 longitude/latitude.")
        normalized.append((float(lon), float(lat)))
    if normalized[0] != normalized[-1]:
        raise HTTPException(status_code=422, detail="AOI polygon must repeat its first coordinate at the end.")
    if len(set(normalized[:-1])) < 3:
        raise HTTPException(status_code=422, detail="AOI must contain at least 3 distinct vertices.")
    return normalized


def _area_km2(coordinates: list[tuple[float, float]]) -> float:
    ring = [*coordinates, coordinates[0]]
    total = 0.0
    for (lon_a, lat_a), (lon_b, lat_b) in zip(ring, ring[1:]):
        delta_lon = math.radians(lon_b - lon_a)
        if delta_lon > math.pi:
            delta_lon -= 2 * math.pi
        if delta_lon < -math.pi:
            delta_lon += 2 * math.pi
        total += delta_lon * (
            math.sin(math.radians(lat_a)) + math.sin(math.radians(lat_b))
        )
    return abs(total) * EARTH_RADIUS_METERS ** 2 / 2 / 1_000_000

def _polygon_wkt(coordinates: list[tuple[float, float]]) -> str:
    return "POLYGON ((" + ", ".join(f"{lon:.8f} {lat:.8f}" for lon, lat in coordinates) + "))"


def _extract_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        candidates = payload
    elif isinstance(payload, dict):
        candidates = payload.get("results") or payload.get("features") or payload.get("items") or []
    else:
        candidates = []
    rows: list[dict[str, Any]] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        properties = item.get("properties")
        row = dict(properties) if isinstance(properties, dict) else dict(item)
        rows.append(row)
    return rows


def _first_string(row: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _maturity(url: str | None) -> str:
    value = (url or "").upper()
    if "NISAR_L2_GCOV_PROVISIONAL_V1" in value:
        return "PROVISIONAL"
    if "NISAR_L2_GCOV_BETA_V1" in value:
        return "BETA"
    return "UNKNOWN"


def _granule_parts(name: str) -> dict[str, str | None]:
    parts = name.split("_")
    if len(parts) < 13 or parts[0] != "NISAR" or "GCOV" not in parts[:5]:
        return {
            "cycle": None, "relative_orbit": None, "flight_direction": None,
            "frame": None, "bandwidth_mode": None, "polarization_code": None,
        }
    return {
        "cycle": parts[4],
        "relative_orbit": parts[5],
        "flight_direction": parts[6],
        "frame": parts[7],
        "bandwidth_mode": parts[8],
        "polarization_code": parts[9],
    }


def _product(row: dict[str, Any]) -> RiverShiftProduct | None:
    name = _first_string(row, ("granuleName", "fileName", "sceneName", "fileID", "productName"))
    level = _first_string(row, ("processingLevel", "productType", "scienceProduct"))
    if not name or (level and level.upper() != "GCOV"):
        return None
    url = _first_string(row, ("url", "downloadUrl", "downloadURL", "productUrl", "product_url"))
    parts = _granule_parts(name)
    size = row.get("sizeMB")
    if isinstance(size, dict):
        byte_values = [
            value.get("bytes")
            for value in size.values()
            if isinstance(value, dict) and isinstance(value.get("bytes"), (int, float)) and value["bytes"] >= 0
        ]
        size_mb = sum(byte_values) / 1_000_000 if byte_values else None
    elif isinstance(size, (int, float)) and size >= 0:
        size_mb = float(size)
    else:
        size_mb = None

    return RiverShiftProduct(
        granule_name=name,
        maturity=_maturity(url),
        download_url=url,
        start_time_utc=_first_string(row, ("startTime", "acquisitionDate")),
        stop_time_utc=_first_string(row, ("stopTime", "endTime")),
        flight_direction=_first_string(row, ("flightDirection", "direction")) or parts["flight_direction"],
        relative_orbit=parts["relative_orbit"],
        cycle=parts["cycle"],
        frame=parts["frame"],
        bandwidth_mode=parts["bandwidth_mode"],
        polarization_code=parts["polarization_code"],
        main_band_polarization=_first_string(row, ("mainBandPolarization", "polarization")),
        size_mb=size_mb,
    )


def search_gcov_catalogue(request: RiverShiftCatalogRequest) -> RiverShiftCatalogResponse:
    coordinates = _validate_coordinates(request.coordinates)
    area = _area_km2(coordinates)
    if not math.isfinite(area) or area <= 0 or area > MAX_AOI_AREA_KM2:
        raise HTTPException(
            status_code=422,
            detail=f"AOI area must be positive and no larger than {MAX_AOI_AREA_KM2:g} km2.",
        )
    if request.end_date < request.start_date:
        raise HTTPException(status_code=422, detail="end_date must not be earlier than start_date.")
    if (request.end_date - request.start_date).days > 366:
        raise HTTPException(status_code=422, detail="Search window cannot exceed 366 days.")

    params = {
        "dataset": "NISAR",
        "processingLevel": "GCOV",
        "intersectsWith": _polygon_wkt(coordinates),
        "start": f"{request.start_date.isoformat()}T00:00:00Z",
        "end": f"{request.end_date.isoformat()}T23:59:59Z",
        "output": "jsonlite",
        "maxResults": str(request.max_results),
    }
    if request.main_band_polarization:
        params["mainBandPolarization"] = request.main_band_polarization
    if request.flight_direction:
        params["flightDirection"] = request.flight_direction

    url = f"{ASF_SEARCH_URL}?{urllib.parse.urlencode(params)}"
    http_request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "SARGuardian-RiverShift/0.1"},
    )
    try:
        with urllib.request.urlopen(http_request, timeout=TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"ASF catalogue returned HTTP {exc.code}.") from None
    except (urllib.error.URLError, TimeoutError):
        raise HTTPException(status_code=504, detail="ASF catalogue request timed out or could not be reached.") from None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=502, detail="ASF catalogue returned an invalid response.") from None

    raw_rows = _extract_rows(payload)
    products: list[RiverShiftProduct] = []
    for row in raw_rows:
        product = _product(row)
        if product is None:
            continue
        if request.maturity != "ALL" and product.maturity != request.maturity:
            continue
        products.append(product)

    warnings = []
    if len(raw_rows) >= request.max_results:
        warnings.append("ASF result cap reached. Narrow the AOI or date range and search again.")
    if any(item.maturity == "UNKNOWN" for item in products):
        warnings.append("Some maturity values are unknown. Do not mix them into a BETA or PROVISIONAL time series.")
    if not products:
        warnings.append("No GCOV products passed the selected AOI, time, polarization and maturity filters.")

    status = "ready" if products else "no_data"
    message = (
        f"Found {len(products)} GCOV product(s). Catalogue discovery only; no data has been downloaded or analysed."
        if products
        else "No matching GCOV products were found for this query."
    )
    return RiverShiftCatalogResponse(
        status=status,
        message=message,
        query={
            "aoi_wkt": _polygon_wkt(coordinates),
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "maturity": request.maturity,
            "main_band_polarization": request.main_band_polarization,
            "flight_direction": request.flight_direction,
            "archive": "ASF DAAC Search API",
        },
        product_count=len(products),
        products=products,
        warnings=warnings,
    )


@router.post("/catalog/search", response_model=RiverShiftCatalogResponse)
def river_shift_catalog_search(request: RiverShiftCatalogRequest) -> RiverShiftCatalogResponse:
    """Public, read-only NISAR GCOV catalogue search. This endpoint never downloads products."""
    return search_gcov_catalogue(request)
