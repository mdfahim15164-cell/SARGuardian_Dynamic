from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.warp import transform_geom


class RasterContractError(ValueError):
    """Raised when rasters cannot be compared without unsafe assumptions."""


def read_band(path: str | Path) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Read band 1 as float64 with a validity mask and a copy of its profile."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Raster does not exist: {path}")

    with rasterio.open(path) as src:
        if src.count < 1:
            raise RasterContractError(f"Raster contains no bands: {path}")
        raw = src.read(1, masked=True)
        array = np.asarray(raw.filled(np.nan), dtype=np.float64)
        valid = (src.dataset_mask() > 0) & np.isfinite(array)
        profile = src.profile.copy()
        profile["transform"] = src.transform
        profile["crs"] = src.crs
        profile["width"] = src.width
        profile["height"] = src.height
        profile["nodata"] = src.nodata
    return array, valid, profile


def assert_same_grid(named_profiles: dict[str, dict[str, Any]]) -> None:
    """Require exact dimensions, affine transform and CRS before pixel comparison."""
    if len(named_profiles) < 2:
        return

    items = list(named_profiles.items())
    base_name, base = items[0]
    if base.get("crs") is None:
        raise RasterContractError(f"{base_name} has no CRS.")

    for name, profile in items[1:]:
        if profile.get("crs") != base.get("crs"):
            raise RasterContractError(
                f"CRS mismatch: {base_name}={base.get('crs')} vs {name}={profile.get('crs')}. "
                "Reproject all inputs to one common projected CRS before analysis."
            )
        if profile.get("width") != base.get("width") or profile.get("height") != base.get("height"):
            raise RasterContractError(f"Raster dimensions differ: {base_name} vs {name}.")
        if profile.get("transform") != base.get("transform"):
            raise RasterContractError(f"Affine grids differ: {base_name} vs {name}.")


def require_projected_metre_grid(profile: dict[str, Any]) -> float:
    """Return pixel area in square metres; reject geographic or non-metre CRS."""
    crs = profile.get("crs")
    if crs is None or not crs.is_projected:
        raise RasterContractError(
            "Area calculations require a projected CRS. Reproject the inputs to a "
            "metric projected CRS such as the appropriate UTM zone."
        )

    units = str(getattr(crs, "linear_units", "") or "").lower()
    if units not in {"metre", "meter", "metres", "meters", "m"}:
        raise RasterContractError(
            f"Area calculations require metre units; source CRS units are {units!r}."
        )

    transform = profile["transform"]
    pixel_area_m2 = abs(transform.a * transform.e - transform.b * transform.d)
    if not np.isfinite(pixel_area_m2) or pixel_area_m2 <= 0:
        raise RasterContractError("Raster pixel area is invalid.")
    return float(pixel_area_m2)


def power_to_db(array: np.ndarray, units: str) -> np.ndarray:
    """Convert positive linear power to dB, or pass through explicitly declared dB."""
    if units == "db":
        return np.asarray(array, dtype=np.float64)
    if units != "linear":
        raise ValueError("units must be either 'linear' or 'db'.")

    result = np.full(array.shape, np.nan, dtype=np.float64)
    positive = np.isfinite(array) & (array > 0)
    result[positive] = 10.0 * np.log10(array[positive])
    return result


def write_mask(path: str | Path, mask: np.ndarray, valid: np.ndarray, profile: dict[str, Any]) -> None:
    """Write a binary UInt8 GeoTIFF: 1=class present, 0=class absent, 255=NoData."""
    output = np.full(mask.shape, 255, dtype=np.uint8)
    output[valid] = 0
    output[np.asarray(mask, dtype=bool) & valid] = 1

    out_profile = {
        key: profile[key]
        for key in ("driver", "height", "width", "transform", "crs")
        if key in profile
    }
    out_profile.update(
        driver="GTiff",
        count=1,
        dtype="uint8",
        nodata=255,
        compress="deflate",
        predictor=2,
        tiled=True,
    )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(output, 1)
        dst.set_band_description(1, "Binary RiverShift classification")


def write_mask_geojson(
    path: str | Path,
    mask: np.ndarray,
    valid: np.ndarray,
    profile: dict[str, Any],
    *,
    class_name: str,
) -> int:
    """Polygonize a binary mask and write GeoJSON in EPSG:4326."""
    src_crs = profile.get("crs")
    if src_crs is None:
        raise RasterContractError("Cannot polygonize a raster without a CRS.")

    features_out = []
    for geometry, value in shapes(
        np.asarray(mask, dtype=np.uint8),
        mask=np.asarray(valid, dtype=bool) & np.asarray(mask, dtype=bool),
        transform=profile["transform"],
    ):
        if int(value) != 1:
            continue
        wgs84_geometry = transform_geom(src_crs, "EPSG:4326", geometry, precision=7)
        features_out.append(
            {
                "type": "Feature",
                "properties": {"class": class_name},
                "geometry": wgs84_geometry,
            }
        )

    collection = {
        "type": "FeatureCollection",
        "name": class_name,
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features_out,
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(collection, indent=2), encoding="utf-8")
    return len(features_out)


def save_json(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")


def safe_float(value: float | np.floating[Any] | None) -> float | None:
    if value is None or not np.isfinite(value):
        return None
    return float(value)
