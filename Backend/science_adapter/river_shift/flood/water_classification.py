"""Open-water candidate classification from NISAR GCOV power."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np


class WaterClassificationError(ValueError):
    """Raised when a water classification input is invalid."""


@dataclass(frozen=True)
class WaterClassification:
    water_mask: np.ndarray
    valid_mask: np.ndarray
    threshold_db: float
    method: str
    valid_pixel_count: int
    water_candidate_count: int


def power_to_db(power: np.ndarray) -> np.ndarray:
    """Convert positive linear power to dB; non-positive/non-finite cells become NaN."""
    array = np.asarray(power, dtype=np.float64)
    if array.ndim != 2:
        raise WaterClassificationError("Power input must be a 2-D array.")
    result = np.full(array.shape, np.nan, dtype=np.float64)
    valid = np.isfinite(array) & (array > 0)
    result[valid] = 10.0 * np.log10(array[valid])
    return result


def otsu_threshold(values: np.ndarray, *, bins: int = 256) -> float:
    """Calculate a one-dimensional Otsu threshold from finite dB values."""
    data = np.asarray(values, dtype=np.float64)
    data = data[np.isfinite(data)]
    if data.size < 2:
        raise WaterClassificationError("At least two finite values are required for Otsu thresholding.")
    if bins < 16 or bins > 4096:
        raise WaterClassificationError("bins must be between 16 and 4096.")

    low, high = np.percentile(data, [2, 98])
    if not np.isfinite(low) or not np.isfinite(high) or high <= low:
        raise WaterClassificationError("Backscatter distribution has insufficient variation for Otsu thresholding.")
    hist, edges = np.histogram(data, bins=bins, range=(low, high))
    hist = hist.astype(np.float64)
    probabilities = hist / hist.sum()
    centers = (edges[:-1] + edges[1:]) / 2.0
    omega = np.cumsum(probabilities)
    mean = np.cumsum(probabilities * centers)
    total_mean = mean[-1]
    denominator = omega * (1.0 - omega)
    between = np.zeros_like(denominator)
    valid = denominator > 0
    between[valid] = (total_mean * omega[valid] - mean[valid]) ** 2 / denominator[valid]
    if not np.any(valid):
        raise WaterClassificationError("Otsu could not separate the backscatter histogram.")
    return float(centers[int(np.argmax(between))])


def classify_open_water(
    power: np.ndarray,
    *,
    valid_mask: np.ndarray | None = None,
    method: Literal["otsu", "fixed"] = "otsu",
    threshold_db: float | None = None,
    minimum_valid_pixels: int = 100,
) -> WaterClassification:
    """Classify low-backscatter open-water candidates from linear GCOV power."""
    if not isinstance(minimum_valid_pixels, int) or minimum_valid_pixels < 2:
        raise WaterClassificationError("minimum_valid_pixels must be an integer of at least 2.")
    db = power_to_db(power)
    valid = np.isfinite(db)
    if valid_mask is not None:
        external = np.asarray(valid_mask)
        if external.shape != db.shape:
            raise WaterClassificationError("valid_mask shape must match power.")
        if external.dtype != np.bool_:
            if not np.issubdtype(external.dtype, np.number) or not np.isfinite(external).all() or not np.isin(external, [0, 1]).all():
                raise WaterClassificationError("valid_mask must contain only Boolean or finite 0/1 values.")
        valid &= external.astype(bool)
    count = int(valid.sum())
    if count < minimum_valid_pixels:
        raise WaterClassificationError(
            f"Only {count} valid pixels; at least {minimum_valid_pixels} are required."
        )

    if method == "otsu":
        if threshold_db is not None:
            raise WaterClassificationError("Do not pass threshold_db with method='otsu'.")
        threshold = otsu_threshold(db[valid])
    elif method == "fixed":
        if threshold_db is None or not np.isfinite(threshold_db):
            raise WaterClassificationError("method='fixed' requires a finite threshold_db.")
        threshold = float(threshold_db)
    else:
        raise WaterClassificationError("method must be 'otsu' or 'fixed'.")

    water = valid & (db <= threshold)
    return WaterClassification(
        water_mask=water,
        valid_mask=valid,
        threshold_db=threshold,
        method=method,
        valid_pixel_count=count,
        water_candidate_count=int(water.sum()),
    )
