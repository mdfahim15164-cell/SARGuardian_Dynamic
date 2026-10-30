"""GeoTIFF export for RiverShift classification masks."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from affine import Affine
from pyproj import CRS

from .gcov_reader import GcovRaster


class RasterExportError(ValueError):
    """Raised when a classification cannot be safely georeferenced."""


def write_water_candidate_geotiff(
    output_path: str | Path,
    gcov: GcovRaster,
    water_mask: np.ndarray,
    valid_mask: np.ndarray,
    *,
    threshold_db: float,
    classification_method: str,
) -> Path:
    """Write a single-band UInt8 GeoTIFF: 0=non-water, 1=water candidate, 255=no-data."""
    try:
        import rasterio
    except ImportError as exc:
        raise RuntimeError("Install rasterio to export RiverShift GeoTIFF outputs.") from exc

    water = np.asarray(water_mask, dtype=bool)
    valid = np.asarray(valid_mask, dtype=bool)
    if water.shape != gcov.shape or valid.shape != gcov.shape:
        raise RasterExportError("water_mask and valid_mask must match the GCOV raster shape.")

    x = np.asarray(gcov.x_coordinates, dtype=np.float64)
    y = np.asarray(gcov.y_coordinates, dtype=np.float64)
    dx_values = np.diff(x)
    dy_values = np.diff(y)
    if not (np.all(dx_values > 0) or np.all(dx_values < 0)):
        raise RasterExportError("xCoordinates must be strictly monotonic.")
    if not (np.all(dy_values > 0) or np.all(dy_values < 0)):
        raise RasterExportError("yCoordinates must be strictly monotonic.")
    dx = float(np.median(np.abs(dx_values)))
    dy = float(np.median(np.abs(dy_values)))
    if not np.allclose(np.abs(dx_values), dx, rtol=1e-4, atol=1e-6):
        raise RasterExportError("xCoordinates are not regular; refusing an affine GeoTIFF transform.")
    if not np.allclose(np.abs(dy_values), dy, rtol=1e-4, atol=1e-6):
        raise RasterExportError("yCoordinates are not regular; refusing an affine GeoTIFF transform.")

    output = np.full(gcov.shape, 255, dtype=np.uint8)
    output[valid] = water[valid].astype(np.uint8)
    if x[0] > x[-1]:
        output = np.fliplr(output)
        x = x[::-1]
    if y[0] < y[-1]:
        output = np.flipud(output)
        y = y[::-1]

    transform = Affine(dx, 0.0, float(x[0]) - dx / 2.0, 0.0, -dy, float(y[0]) + dy / 2.0)
    crs = CRS.from_wkt(gcov.crs_wkt)
    if not crs.is_projected:
        raise RasterExportError("RiverShift export currently requires a projected GCOV grid.")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "height": output.shape[0],
        "width": output.shape[1],
        "count": 1,
        "dtype": "uint8",
        "crs": crs,
        "transform": transform,
        "nodata": 255,
        "compress": "deflate",
    }
    with rasterio.open(path, "w", **profile) as dataset:
        dataset.write(output, 1)
        dataset.set_band_description(1, "open_water_candidate")
        dataset.update_tags(
            product="RiverShift open-water candidate classification",
            source_product="NISAR GCOV",
            source_path=gcov.source_path,
            frequency=gcov.frequency,
            covariance_term=gcov.covariance_term,
            source_units=gcov.units or "not recorded in source layer",
            classification_method=classification_method,
            threshold_db=str(float(threshold_db)),
            water_pixel_value="1",
            non_water_pixel_value="0",
            nodata_pixel_value="255",
            interpretation="candidate open water; not independently validated",
        )
    return path
