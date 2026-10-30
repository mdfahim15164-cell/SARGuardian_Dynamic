from __future__ import annotations

import csv
import json
import statistics
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
from rasterio.crs import CRS
from rasterio.warp import transform_geom
from shapely.geometry import LineString, shape
from shapely.ops import unary_union


def _load_collection(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
        raise ValueError(f"{path} must be a GeoJSON FeatureCollection.")
    return payload


def _require_metric_crs(crs_text: str) -> CRS:
    crs = CRS.from_user_input(crs_text)
    if not crs.is_projected:
        raise ValueError("Transect analysis requires a projected CRS.")
    units = str(crs.linear_units or "").lower()
    if units not in {"metre", "meter", "metres", "meters", "m"}:
        raise ValueError(f"Transect analysis requires metre units, not {units!r}.")
    return crs


def _load_bankline(path: str | Path):
    collection = _load_collection(path)
    lines = []
    for feature in collection["features"]:
        geometry = shape(feature.get("geometry"))
        if geometry.geom_type == "LineString" and not geometry.is_empty:
            lines.append(geometry)
        elif geometry.geom_type == "MultiLineString" and not geometry.is_empty:
            lines.extend(list(geometry.geoms))
        else:
            raise ValueError("Bankline GeoJSON must contain only LineString or MultiLineString features.")
    if not lines:
        raise ValueError(f"No bankline features found in {path}.")
    merged = unary_union(lines)
    if merged.is_empty:
        raise ValueError(f"Bankline geometry is empty: {path}.")
    return merged


def _point_parts(geometry) -> list[Any]:
    if geometry.is_empty:
        return []
    if geometry.geom_type == "Point":
        return [geometry]
    if geometry.geom_type in {"MultiPoint", "GeometryCollection"}:
        result = []
        for part in geometry.geoms:
            result.extend(_point_parts(part))
        return result
    return []


def _unique_intersection_distance(transect: LineString, bankline) -> tuple[float | None, str]:
    intersection = transect.intersection(bankline)
    points = _point_parts(intersection)
    if len(points) != 1:
        return None, "no_unique_intersection"
    distance = float(transect.project(points[0]))
    return distance, "ok"


def _safe(value: float | None) -> float | None:
    if value is None or not np.isfinite(value):
        return None
    return float(value)


def measure_bankline_migration(
    *,
    before_bankline_path: str,
    after_bankline_path: str,
    transects_path: str,
    input_crs: str,
    before_date: str,
    after_date: str,
    positive_direction_label: str,
    source_mission: str,
    source_product: str,
    maturity: str,
    output_dir: str,
) -> dict[str, Any]:
    """Measure signed bankline movement along user-oriented transects.

    Each transect must intersect each bankline exactly once. Its digitized start
    and end points define the positive direction. Displacement is post distance
    minus pre distance measured from the transect start.
    """
    crs = _require_metric_crs(input_crs)
    start = date.fromisoformat(before_date)
    end = date.fromisoformat(after_date)
    elapsed_days = (end - start).days
    if elapsed_days <= 0:
        raise ValueError("after_date must be later than before_date.")
    if not positive_direction_label.strip():
        raise ValueError("positive_direction_label is required.")
    if maturity not in {"BETA", "PROVISIONAL", "UNKNOWN"}:
        raise ValueError("maturity must be BETA, PROVISIONAL or UNKNOWN.")

    before_bankline = _load_bankline(before_bankline_path)
    after_bankline = _load_bankline(after_bankline_path)
    transect_collection = _load_collection(transects_path)

    rows = []
    output_features = []
    for index, feature in enumerate(transect_collection["features"], start=1):
        properties = feature.get("properties") or {}
        transect_id = str(properties.get("transect_id") or properties.get("id") or f"T{index:03d}")
        geometry = shape(feature.get("geometry"))
        if geometry.geom_type != "LineString" or geometry.is_empty or geometry.length <= 0:
            rows.append({
                "transect_id": transect_id,
                "status": "invalid_transect_geometry",
                "before_chainage_m": None,
                "after_chainage_m": None,
                "signed_displacement_m": None,
                "mean_net_rate_m_per_year": None,
            })
            continue

        before_chainage, before_status = _unique_intersection_distance(geometry, before_bankline)
        after_chainage, after_status = _unique_intersection_distance(geometry, after_bankline)
        status = "ok" if before_status == "ok" and after_status == "ok" else (
            "before_" + before_status if before_status != "ok" else "after_" + after_status
        )
        displacement = after_chainage - before_chainage if status == "ok" else None
        years = elapsed_days / 365.25
        rate = displacement / years if displacement is not None else None
        row = {
            "transect_id": transect_id,
            "status": status,
            "before_chainage_m": _safe(before_chainage),
            "after_chainage_m": _safe(after_chainage),
            "signed_displacement_m": _safe(displacement),
            "mean_net_rate_m_per_year": _safe(rate),
            "positive_direction_label": positive_direction_label,
        }
        rows.append(row)

        geographic = transform_geom(crs, "EPSG:4326", geometry.__geo_interface__, precision=7)
        output_features.append({
            "type": "Feature",
            "properties": row,
            "geometry": geographic,
        })

    valid = [row for row in rows if row["status"] == "ok"]
    displacements = [float(row["signed_displacement_m"]) for row in valid]
    rates = [float(row["mean_net_rate_m_per_year"]) for row in valid]
    summary: dict[str, Any] = {
        "schema_version": 1,
        "engine": "RiverShift",
        "analysis_type": "bankline_migration",
        "source": {
            "mission": source_mission,
            "product": source_product,
            "maturity": maturity.upper(),
            "input_type": "user_digitized_banklines_and_transects",
        },
        "inputs": {
            "before_bankline": str(before_bankline_path),
            "after_bankline": str(after_bankline_path),
            "transects": str(transects_path),
            "input_crs": crs.to_string(),
            "before_date": start.isoformat(),
            "after_date": end.isoformat(),
            "elapsed_days": elapsed_days,
            "positive_direction_label": positive_direction_label,
            "transect_orientation": "positive from each LineString first coordinate to last coordinate",
        },
        "method": {
            "measurement": "signed_chainage_difference_along_user_supplied_transects",
            "formula": "after_chainage_m - before_chainage_m",
            "rate_formula": "signed_displacement_m / (elapsed_days / 365.25)",
            "intersection_rule": "each transect must intersect each bankline exactly once",
        },
        "metrics": {
            "transect_count": len(rows),
            "valid_transect_count": len(valid),
            "invalid_transect_count": len(rows) - len(valid),
            "mean_signed_displacement_m": _safe(statistics.mean(displacements)) if valid else None,
            "median_signed_displacement_m": _safe(statistics.median(displacements)) if valid else None,
            "p95_absolute_displacement_m": _safe(float(np.percentile(np.abs(displacements), 95))) if valid else None,
            "mean_net_rate_m_per_year": _safe(statistics.mean(rates)) if valid else None,
            "channelward_count": sum(1 for value in displacements if value > 0),
            "landward_count": sum(1 for value in displacements if value < 0),
            "unchanged_count": sum(1 for value in displacements if value == 0),
        },
        "quality": {
            "status": "TRANSECT_MEASURED_REQUIRES_BANKLINE_VALIDATION" if valid else "NO_VALID_TRANSECTS",
            "warnings": [
                "Positive/negative meaning follows the user-declared transect orientation label. Verify every transect starts on the documented side and ends on the opposite side.",
                "Every transect must intersect each selected bankline exactly once; multiple-channel intersections are marked invalid.",
                "Rates are mean net displacement between two observation dates, not a long-term trend or a forecast.",
                "Banklines are user-digitized inputs and must be independently reviewed against the source satellite imagery.",
                "The method measures movement along supplied cross-sections; it does not automatically extract the active channel belt.",
            ],
        },
        "transects": rows,
        "outputs": {
            "csv": "bankline_migration.csv",
            "geojson": "bankline_migration_transects.geojson",
        },
    }

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "bankline_migration.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = [
            "transect_id", "status", "before_chainage_m", "after_chainage_m",
            "signed_displacement_m", "mean_net_rate_m_per_year", "positive_direction_label",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    (out / "bankline_migration_transects.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": output_features}, indent=2),
        encoding="utf-8",
    )
    (out / "bankline_migration_summary.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    return summary
