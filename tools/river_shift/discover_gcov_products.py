#!/usr/bin/env python3
"""Discover NISAR GCOV products intersecting a WGS84 AOI through the ASF Search API."""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path
from typing import Any

from shapely import wkt as shapely_wkt
from shapely.geometry import Polygon

ASF_SEARCH_URL = "https://api.daac.asf.alaska.edu/services/search/param"
MATURITY_PATTERN = re.compile(r"NISAR_L2_GCOV_(BETA|PROVISIONAL)_V1", re.IGNORECASE)


def validate_aoi(value: str) -> str:
    geometry = shapely_wkt.loads(value)
    if not isinstance(geometry, Polygon) or geometry.is_empty or not geometry.is_valid:
        raise ValueError("AOI must be one valid, non-empty WGS84 POLYGON.")
    if geometry.area <= 0:
        raise ValueError("AOI polygon must have positive area.")
    return geometry.wkt


def extract_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        candidates = payload
    elif isinstance(payload, dict):
        candidates = payload.get("results") or payload.get("features") or payload.get("items") or []
    else:
        candidates = []

    rows = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        properties = item.get("properties")
        row = dict(properties) if isinstance(properties, dict) else dict(item)
        for key in ("geometry", "id", "type"):
            if key in item and key not in row:
                row[key] = item[key]
        rows.append(row)
    return rows


def first_string(row: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def detect_maturity(url: str | None, row: dict[str, Any]) -> str:
    values = [url or ""]
    values.extend(str(row.get(key, "")) for key in ("granuleName", "fileName", "productName", "collectionName"))
    for value in values:
        match = MATURITY_PATTERN.search(value)
        if match:
            return match.group(1).upper()
    return "UNKNOWN"


def parse_granule_metadata(name: str) -> dict[str, str | None]:
    """Parse the official 18-token NISAR single-acquisition GCOV filename."""
    base_name = name.removesuffix(".h5")
    parts = base_name.split("_")
    if (
        len(parts) != 18
        or parts[0] != "NISAR"
        or parts[1] != "L2"
        or parts[2] not in {"PR", "UR", "OD"}
        or parts[3] != "GCOV"
        or parts[6] not in {"A", "D"}
        or parts[15] not in {"F", "P"}
    ):
        raise ValueError(f"Not a supported NISAR L2 GCOV granule name: {name}")

    try:
        start = datetime.strptime(parts[11], "%Y%m%dT%H%M%S")
        end = datetime.strptime(parts[12], "%Y%m%dT%H%M%S")
    except ValueError:
        raise ValueError(f"Invalid acquisition timestamp in GCOV granule name: {name}") from None
    if end < start:
        raise ValueError(f"GCOV acquisition end precedes acquisition start: {name}")

    return {
        "cycle": parts[4],
        "relative_orbit": parts[5],
        "orbit_direction": parts[6],
        "frame": parts[7],
        "bandwidth_mode": parts[8],
        "polarization_code": parts[9],
        "acquisition_start_utc": parts[11],
        "acquisition_end_utc": parts[12],
        "crid": parts[13],
        "orbit_accuracy": parts[14],
        "frame_coverage": "FULL" if parts[15] == "F" else "PARTIAL",
        "science_data_system": parts[16],
        "product_counter": parts[17],
    }


def normalize_product(row: dict[str, Any]) -> dict[str, Any] | None:
    name = first_string(row, ("granuleName", "fileName", "sceneName", "fileID", "productName"))
    product_level = first_string(row, ("processingLevel", "productType", "scienceProduct"))
    if not name or (product_level and product_level.upper() != "GCOV"):
        return None

    name = name.removesuffix(".h5")
    url = first_string(row, ("url", "downloadUrl", "downloadURL", "productUrl", "product_url"))
    metadata = parse_granule_metadata(name)
    maturity = detect_maturity(url, row)
    collection = first_string(row, ("collectionName", "collection", "shortName"))
    if maturity == "UNKNOWN" and collection:
        match = MATURITY_PATTERN.search(collection)
        if match:
            maturity = match.group(1).upper()
    if not url and maturity in {"BETA", "PROVISIONAL"}:
        url = (
            "https://nisar.asf.earthdatacloud.nasa.gov/NISAR/"
            f"NISAR_L2_GCOV_{maturity}_V1/{name}/{name}.h5"
        )
    start_time = first_string(row, ("startTime", "acquisitionDate", "start_date")) or metadata["acquisition_start_utc"]
    stop_time = first_string(row, ("stopTime", "endTime", "stop_date")) or metadata["acquisition_end_utc"]
    size = row.get("sizeMB")
    if isinstance(size, dict):
        sizes = [
            item.get("bytes")
            for item in size.values()
            if isinstance(item, dict) and isinstance(item.get("bytes"), (int, float))
        ]
        size_mb = sum(sizes) / 1_000_000 if sizes else None
    elif isinstance(size, (int, float)):
        size_mb = float(size)
    else:
        size_mb = None

    direction = first_string(row, ("flightDirection", "direction")) or metadata["orbit_direction"]
    if direction:
        direction = {"A": "ASCENDING", "D": "DESCENDING", "ASC": "ASCENDING", "DESC": "DESCENDING"}.get(direction.upper(), direction.upper())
    frame_coverage_raw = first_string(row, ("frameCoverage", "coverage"))
    frame_coverage = (
        {"F": "FULL", "FULL": "FULL", "P": "PARTIAL", "PARTIAL": "PARTIAL"}.get(frame_coverage_raw.upper())
        if frame_coverage_raw else metadata["frame_coverage"]
    )

    return {
        "granule_name": name,
        "product": "GCOV",
        "maturity": maturity,
        "download_url": url,
        "start_time_utc": start_time,
        "stop_time_utc": stop_time,
        "flight_direction": direction,
        "frame_coverage": frame_coverage,
        "footprint": row.get("geometry") or row.get("footprint"),
        "main_band_polarization": first_string(row, ("mainBandPolarization", "polarization")) or {
            "SH": "HH", "SV": "VV", "DH": "HH+HV", "DV": "VV+VH",
            "CL": "LH+LV", "CR": "RH+RV",
        }.get((metadata["polarization_code"] or "")[:2]),
        "size_mb": size_mb,
        **metadata,
    }


def search_catalogue(
    aoi_wkt: str,
    start_date: date,
    end_date: date,
    maturity: str,
    main_band_polarization: str | None,
    flight_direction: str | None,
    max_results: int,
    timeout: int,
    frame_coverage: str = "ALL",
) -> dict[str, Any]:
    params = {
        "dataset": "NISAR",
        "processingLevel": "GCOV",
        "intersectsWith": aoi_wkt,
        "start": f"{start_date.isoformat()}T00:00:00Z",
        "end": f"{end_date.isoformat()}T23:59:59Z",
        "output": "json",
        "maxResults": str(max_results),
    }
    if main_band_polarization:
        params["mainBandPolarization"] = main_band_polarization
    if flight_direction:
        params["flightDirection"] = flight_direction
    if frame_coverage not in {"ALL", "FULL", "PARTIAL"}:
        raise ValueError("frame-coverage must be ALL, FULL or PARTIAL.")
    if frame_coverage != "ALL":
        params["frameCoverage"] = frame_coverage

    query_url = f"{ASF_SEARCH_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        query_url,
        headers={"Accept": "application/json", "User-Agent": "SARGuardian-RiverShift/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"ASF Search API returned HTTP {exc.code}.") from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError("ASF Search API could not be reached before the timeout.") from None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise RuntimeError("ASF Search API returned invalid JSON.") from None

    raw_rows = extract_rows(payload)
    products = []
    for row in raw_rows:
        item = normalize_product(row)
        if not item:
            continue
        if maturity != "ALL" and item["maturity"] != maturity:
            continue
        products.append(item)

    products.sort(key=lambda item: str(item.get("start_time_utc") or ""), reverse=False)
    warnings = []
    unknown_count = sum(1 for item in products if item["maturity"] == "UNKNOWN")
    if unknown_count:
        warnings.append(
            f"{unknown_count} product(s) have unknown maturity. Do not mix them with BETA or PROVISIONAL products."
        )
    if len(raw_rows) >= max_results:
        warnings.append("ASF result cap was reached; narrow the AOI or acquisition window.")
    if not products:
        warnings.append(
            "No products passed the requested product type and maturity filters. This is a catalogue result, not proof of no NISAR acquisitions."
        )

    return {
        "schema_version": 1,
        "mission": "NISAR",
        "agency": "NASA-ISRO",
        "archive": "Alaska Satellite Facility DAAC",
        "product": "GCOV",
        "maturity_filter": maturity,
        "query": {
            "aoi_wkt": aoi_wkt,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "main_band_polarization": main_band_polarization,
            "frame_coverage": frame_coverage,
            "flight_direction": flight_direction,
            "max_results": max_results,
            "endpoint": ASF_SEARCH_URL,
            "response_format": "json",
        },
        "raw_record_count": len(raw_rows),
        "product_count": len(products),
        "products": products,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aoi-wkt", required=True, help="One valid WGS84 POLYGON WKT.")
    parser.add_argument("--start-date", required=True, type=date.fromisoformat)
    parser.add_argument("--end-date", required=True, type=date.fromisoformat)
    parser.add_argument("--maturity", choices=("BETA", "PROVISIONAL", "ALL"), default="PROVISIONAL")
    parser.add_argument("--main-band-polarization", choices=("HH", "HH+HV", "HH+VV", "HH+HV+VH+VV", "VV", "VV+VH", "LH+LV", "RH+RV"))
    parser.add_argument("--flight-direction", choices=("ASCENDING", "DESCENDING"))
    parser.add_argument("--frame-coverage", choices=("ALL", "FULL", "PARTIAL"), default="ALL")
    parser.add_argument("--max-results", type=int, default=500)
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--out", required=True, help="Output JSON manifest path.")
    args = parser.parse_args()

    try:
        if args.end_date < args.start_date:
            raise ValueError("end-date must not be earlier than start-date.")
        if not 1 <= args.max_results <= 2000:
            raise ValueError("max-results must be between 1 and 2000.")
        aoi = validate_aoi(args.aoi_wkt)
        result = search_catalogue(
            aoi, args.start_date, args.end_date, args.maturity,
            args.main_band_polarization, args.flight_direction,
            args.max_results, args.timeout, args.frame_coverage,
        )
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"RIVERSHIFT_GCOV_PRODUCTS={result['product_count']}")
        print(f"RIVERSHIFT_CATALOGUE_MANIFEST={output}")
        for warning in result["warnings"]:
            print(f"WARNING={warning}", file=sys.stderr)
        return 0
    except Exception as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
