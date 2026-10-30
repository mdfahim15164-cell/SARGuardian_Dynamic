"""Read-only ASF NISAR GCOV catalogue discovery.

This module discovers candidate products only. It does not download or process them.
"""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Any, Callable

from shapely import wkt
from shapely.geometry import Polygon


ALLOWED_MATURITY = {"PROVISIONAL", "BETA"}


class CatalogRequestError(ValueError):
    """Raised when a GCOV catalogue request is invalid."""


def _validate_request(
    aoi_wkt: str,
    start_date: date | str,
    end_date: date | str,
    maturity: str,
    max_results: int,
) -> tuple[str, date, date, str, int]:
    try:
        geometry = wkt.loads(aoi_wkt)
    except Exception as exc:
        raise CatalogRequestError("AOI must be a valid WKT polygon.") from exc

    if not isinstance(geometry, Polygon) or geometry.is_empty or not geometry.is_valid:
        raise CatalogRequestError("AOI must be one valid, non-empty Polygon without self-intersections.")
    if geometry.area <= 0:
        raise CatalogRequestError("AOI polygon must have positive area.")
    if geometry.bounds[0] < -180 or geometry.bounds[2] > 180 or geometry.bounds[1] < -90 or geometry.bounds[3] > 90:
        raise CatalogRequestError("AOI must use WGS84 longitude/latitude coordinates.")

    try:
        start = date.fromisoformat(start_date) if isinstance(start_date, str) else start_date
        end = date.fromisoformat(end_date) if isinstance(end_date, str) else end_date
    except (TypeError, ValueError) as exc:
        raise CatalogRequestError("Dates must be valid YYYY-MM-DD dates.") from exc

    if end < start:
        raise CatalogRequestError("end_date must not be earlier than start_date.")
    if (end - start).days > 366:
        raise CatalogRequestError("A single catalogue request cannot exceed 366 days.")
    maturity = maturity.upper().strip()
    if maturity not in ALLOWED_MATURITY:
        raise CatalogRequestError("maturity must be PROVISIONAL or BETA.")
    if not isinstance(max_results, int) or not 1 <= max_results <= 500:
        raise CatalogRequestError("max_results must be between 1 and 500.")
    return geometry.wkt, start, end, maturity, max_results


def _as_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def _properties(product: Any) -> dict[str, Any]:
    props = getattr(product, "properties", None)
    if isinstance(props, dict):
        return props
    if isinstance(product, dict):
        return product.get("properties", product)
    return {}


def search_gcov(
    aoi_wkt: str,
    start_date: date | str,
    end_date: date | str,
    *,
    maturity: str = "PROVISIONAL",
    max_results: int = 100,
    search_function: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Search ASF for NISAR GCOV scenes intersecting a WGS84 polygon.

    An injectable search_function makes the catalogue contract unit-testable
    without network calls. In production, ASF's asf_search package is used.
    """
    geometry_wkt, start, end, maturity, max_results = _validate_request(
        aoi_wkt, start_date, end_date, maturity, max_results
    )

    if search_function is None:
        try:
            import asf_search as asf
        except ImportError as exc:
            raise RuntimeError(
                "asf_search is required for live GCOV catalogue discovery. "
                "Install river_shift/requirements-river-shift.txt."
            ) from exc
        search_function = asf.search

    results = search_function(
        dataset="NISAR",
        processingLevel="GCOV",
        dataMaturity=maturity,
        intersectsWith=geometry_wkt,
        start=f"{start.isoformat()}T00:00:00Z",
        end=f"{end.isoformat()}T23:59:59Z",
        maxResults=max_results,
    )

    scenes: list[dict[str, Any]] = []
    for product in results:
        props = _properties(product)
        name = props.get("fileName") or props.get("granuleName") or props.get("sceneName")
        if not name:
            continue
        scenes.append({
            "granule_name": str(name),
            "product_id": props.get("sceneName") or props.get("granuleName"),
            "product_type": props.get("processingLevel") or "GCOV",
            "data_maturity": props.get("dataMaturity") or maturity,
            "start_time": _as_iso(props.get("startTime") or props.get("start")),
            "stop_time": _as_iso(props.get("stopTime") or props.get("endTime")),
            "flight_direction": props.get("flightDirection"),
            "path_number": props.get("pathNumber"),
            "frame_number": props.get("frameNumber"),
            "polarization": props.get("polarization"),
            "url": props.get("url"),
            "size_bytes": props.get("bytes"),
        })

    scenes.sort(key=lambda item: (item.get("start_time") or "", item["granule_name"]))
    return {
        "dataset": "NISAR",
        "processing_level": "GCOV",
        "data_maturity": maturity,
        "aoi_wkt": geometry_wkt,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "result_count": len(scenes),
        "limit": max_results,
        "truncated_possible": len(scenes) >= max_results,
        "catalogue_only": True,
        "data_downloaded": False,
        "scientific_analysis_performed": False,
        "scenes": scenes,
        "warnings": [
            "Catalogue presence does not prove that scenes form a comparable time series.",
            "Check track, frame, frequency, polarization, processing maturity and CRID before change analysis.",
        ],
    }
