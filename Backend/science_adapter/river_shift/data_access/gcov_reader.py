"""Strict reader for NISAR GCOV diagonal backscatter layers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import h5py
import numpy as np
from pyproj import CRS


VALID_DIAGONAL_TERMS = {"HHHH", "HVHV", "VVVV", "VHVH", "RHRH", "RVRV"}


class GcovReadError(ValueError):
    """Raised when a NISAR GCOV product does not meet the reader contract."""


@dataclass(frozen=True)
class GcovRaster:
    power: np.ndarray
    valid_mask: np.ndarray
    x_coordinates: np.ndarray
    y_coordinates: np.ndarray
    crs_wkt: str
    epsg: int | None
    frequency: str
    covariance_term: str
    source_path: str
    units: str | None

    @property
    def shape(self) -> tuple[int, int]:
        return self.power.shape

    @property
    def crs(self) -> CRS:
        return CRS.from_wkt(self.crs_wkt)

    @property
    def pixel_area_m2(self) -> float:
        dx = float(np.median(np.diff(self.x_coordinates)))
        dy = float(np.median(np.diff(self.y_coordinates)))
        crs = self.crs
        if not crs.is_projected:
            raise GcovReadError("GCOV grid must use a projected CRS to derive pixel area.")
        axes = crs.axis_info
        if len(axes) < 2:
            raise GcovReadError("Projected CRS does not expose two axis unit conversion factors.")
        factor_x = float(axes[0].unit_conversion_factor or 1.0)
        factor_y = float(axes[1].unit_conversion_factor or 1.0)
        return abs(dx * factor_x * dy * factor_y)


def _decode_scalar(value: Any) -> Any:
    if isinstance(value, np.ndarray) and value.shape == ():
        value = value.item()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip("\x00 ")
    if isinstance(value, np.bytes_):
        return bytes(value).decode("utf-8", errors="replace").strip("\x00 ")
    return value


def _resolve_crs(projection: h5py.Dataset) -> CRS:
    """Resolve CRS from EPSG, WKT or CF grid-mapping metadata without guessing."""
    raw = _decode_scalar(projection[()])
    attributes = {
        str(key): _decode_scalar(value)
        for key, value in projection.attrs.items()
    }

    candidates: list[Any] = [raw]
    for key in ("epsg_code", "epsgCode", "spatial_ref", "crs_wkt", "wkt"):
        if key in attributes:
            candidates.append(attributes[key])

    for candidate in candidates:
        if candidate is None:
            continue
        if isinstance(candidate, (int, np.integer)):
            try:
                return CRS.from_epsg(int(candidate))
            except Exception:
                continue
        text = str(candidate).strip()
        if not text:
            continue
        try:
            return CRS.from_user_input(text)
        except Exception:
            pass

    # NISAR products use CF metadata conventions. CRS.from_cf expects the
    # complete grid-mapping attribute dictionary, not an inferred UTM zone.
    cf_attributes = {
        key: value
        for key, value in attributes.items()
        if value is not None and key not in {"_FillValue", "long_name", "description"}
    }
    if "grid_mapping_name" in cf_attributes:
        try:
            return CRS.from_cf(cf_attributes)
        except Exception:
            pass

    raise GcovReadError(
        "Could not resolve CRS from the GCOV projection dataset (EPSG, WKT or CF attributes)."
    )


def _check_regular_axis(values: np.ndarray, name: str) -> None:
    if values.ndim != 1 or values.size < 2 or not np.all(np.isfinite(values)):
        raise GcovReadError(f"{name} must be a finite 1-D coordinate array with at least 2 values.")
    delta = np.diff(values.astype(np.float64))
    if not (np.all(delta > 0) or np.all(delta < 0)):
        raise GcovReadError(f"{name} must be strictly monotonic.")
    median = float(np.median(np.abs(delta)))
    if median <= 0 or not np.allclose(np.abs(delta), median, rtol=1e-4, atol=1e-6):
        raise GcovReadError(f"{name} is not regularly spaced; an affine raster transform is unsafe.")


def read_gcov(
    source_path: str | Path,
    *,
    frequency: str = "A",
    covariance_term: str = "VVVV",
) -> GcovRaster:
    """Load one real-valued GCOV diagonal term and its geospatial grid metadata.

    The returned array is not resampled or thresholded. Its numeric values remain
    in the source product's units (GCOV diagonal layers are gamma0 power).
    """
    frequency = frequency.upper()
    covariance_term = covariance_term.upper()
    if frequency not in {"A", "B"}:
        raise GcovReadError("frequency must be A or B.")
    if covariance_term not in VALID_DIAGONAL_TERMS:
        raise GcovReadError(f"covariance_term must be one of {sorted(VALID_DIAGONAL_TERMS)}.")

    path = Path(source_path)
    if not path.is_file():
        raise GcovReadError(f"GCOV file does not exist: {path}")

    grid_path = f"/science/LSAR/GCOV/grids/frequency{frequency}"
    data_path = f"{grid_path}/{covariance_term}"

    try:
        with h5py.File(path, "r") as h5:
            required = (
                data_path,
                f"{grid_path}/xCoordinates",
                f"{grid_path}/yCoordinates",
                f"{grid_path}/projection",
            )
            for dataset_path in required:
                if dataset_path not in h5:
                    raise GcovReadError(f"Required GCOV dataset is missing: {dataset_path}")

            dataset = h5[data_path]
            if np.issubdtype(dataset.dtype, np.complexfloating):
                raise GcovReadError("A diagonal covariance power layer must be real-valued.")
            power = np.asarray(dataset[()], dtype=np.float32)
            x = np.asarray(h5[f"{grid_path}/xCoordinates"][()], dtype=np.float64)
            y = np.asarray(h5[f"{grid_path}/yCoordinates"][()], dtype=np.float64)
            crs = _resolve_crs(h5[f"{grid_path}/projection"])
            units_value = dataset.attrs.get("units")
            units = str(_decode_scalar(units_value)) if units_value is not None else None

            if power.ndim != 2:
                raise GcovReadError("GCOV covariance layer must be a 2-D raster.")
            if power.shape != (y.size, x.size):
                raise GcovReadError(
                    f"Raster shape {power.shape} does not match y/x coordinate sizes {(y.size, x.size)}."
                )
            _check_regular_axis(x, "xCoordinates")
            _check_regular_axis(y, "yCoordinates")

            # A strictly positive finite covariance value is numerically valid.
            # numberOfLooks is an additional validity constraint when supplied.
            valid = np.isfinite(power) & (power > 0)
            looks_path = f"{grid_path}/numberOfLooks"
            if looks_path in h5:
                looks = np.asarray(h5[looks_path][()], dtype=np.float32)
                if looks.shape != power.shape:
                    raise GcovReadError("numberOfLooks shape does not match the covariance layer.")
                valid &= np.isfinite(looks) & (looks > 0)

    except OSError as exc:
        raise GcovReadError(f"Could not open GCOV HDF5 product: {exc}") from exc

    epsg = crs.to_epsg()
    return GcovRaster(
        power=power,
        valid_mask=valid,
        x_coordinates=x,
        y_coordinates=y,
        crs_wkt=crs.to_wkt(),
        epsg=int(epsg) if epsg is not None else None,
        frequency=frequency,
        covariance_term=covariance_term,
        source_path=str(path),
        units=units,
    )


def inspect_gcov(source_path: str | Path) -> dict[str, Any]:
    """Return an inventory of candidate GCOV diagonal layers in a file."""
    path = Path(source_path)
    if not path.is_file():
        raise GcovReadError(f"GCOV file does not exist: {path}")
    inventory: list[dict[str, Any]] = []
    with h5py.File(path, "r") as h5:
        root = "/science/LSAR/GCOV/grids"
        if root not in h5:
            raise GcovReadError("This HDF5 file does not expose the documented LSAR GCOV grid group.")
        for frequency in ("A", "B"):
            group_path = f"{root}/frequency{frequency}"
            if group_path not in h5:
                continue
            group = h5[group_path]
            for term in sorted(VALID_DIAGONAL_TERMS):
                if term in group and isinstance(group[term], h5py.Dataset):
                    inventory.append({
                        "frequency": frequency,
                        "covariance_term": term,
                        "shape": list(group[term].shape),
                        "dtype": str(group[term].dtype),
                    })
    return {"source_path": str(path), "product_family": "GCOV", "layers": inventory}
