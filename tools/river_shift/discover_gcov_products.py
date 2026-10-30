#!/usr/bin/env python3
"""Discover NISAR GCOV products intersecting a WGS84 AOI through the ASF Search API."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
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
    parts = name.split("_")
    if len(parts) < 13 or parts[0] != "NISAR" or "GCOV" not in parts[:5]:
        return {
            "cycle": None,
            "relative_orbit": None,
            "orbit_direction": None,
            "frame": None,
            "bandwidth_mode": None,
            "polarization_code": None,
            "acquisition_start_utc": None,
            "acquisition_end_utc": None,
        }
    return {
        "cycle": parts[4] if len(parts) > 4 else None,
        "relative_orbit": parts[5] if len(parts) > 5 else None,
        "orbit_direction": parts[6] if len(parts) > 6 else None,
        "frame": parts[7] if len(parts) > 7 else None,
        "bandwidth_mode": parts[8] if len(parts) > 8 else None,
        "polarization_code": parts[9] if len(parts) > 9 else None,
        "acquisition_start_utc": parts[11] if len(parts) > 11 else None,
        "acquisition_end_utc": parts[12] if len(parts) > 12 else None,
    }


def normalize_product(row: dict[str, Any]) -> dict[str, Any] | None:
    name = first_string(row, ("granuleName", "fileName", "sceneName", "fileID", "productName"))
    product_level = first_string(row, ("processingLevel", "productType", "scienceProduct"))
    if not name or (product_level and product_level.upper() != "GCOV"):
        return None

    url = first_string(row, ("url", "downloadUrl", "downloadURL", "productUrl", "product_url"))
    metadata = parse_granule_metadata(name)
    start_time = first_string(row, ("startTime", "acquisitionDate", "start_date"))
    stop_time = first_string(row, ("stopTime", "endTime", "stop_date"))
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
        direction = {"A": "ASCENDING", "D": "DESCENDING"}.get(direction.upper(), direction.upper())

    return {
        "granule_name": name,
        "product": "GCOV",
        "maturity": detect_maturity(url, row),
        "download_url": url,
        "start_time_utc": start_time,
        "stop_time_utc": stop_time,
        "flight_direction": direction,
        "main_band_polarization": first_string(row, ("mainBandPolarization", "polarization")),
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
) -> dict[str, Any]:
    params = {
        "dataset": "NISAR",
        "processingLevel": "GCOV",
        "intersectsWith": aoi_wkt,
        "start": f"{start_date.isoformat()}T00:00:00Z",
        "end": f"{end_date.isoformat()}T23:59:59Z",
        "output": "jsonlite",
        "maxResults": str(max_results),
    }
    if main_band_polarization:
        params["mainBandPolarization"] = main_band_polarization
    if flight_direction:
        params["flightDirection"] = flight_direction

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
            "flight_direction": flight_direction,
            "max_results": max_results,
            "endpoint": ASF_SEARCH_URL,
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
            args.max_results, args.timeout,
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
