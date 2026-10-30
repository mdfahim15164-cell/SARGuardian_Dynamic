"""Area accounting for event-related new inundation."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


class InundationError(ValueError):
    """Raised for incompatible water masks or pixel area."""


@dataclass(frozen=True)
class InundationResult:
    newly_inundated_mask: np.ndarray
    common_valid_mask: np.ndarray
    baseline_water_area_km2: float
    event_water_area_km2: float
    newly_inundated_area_km2: float
    water_area_change_percent: float | None
    valid_pixel_count: int


def calculate_inundation(
    baseline_water: np.ndarray,
    event_water: np.ndarray,
    *,
    pixel_area_m2: float,
    baseline_valid: np.ndarray | None = None,
    event_valid: np.ndarray | None = None,
) -> InundationResult:
    """Calculate newly inundated area on a common, compatible raster grid."""
    baseline = np.asarray(baseline_water, dtype=bool)
    event = np.asarray(event_water, dtype=bool)
    if baseline.ndim != 2 or event.ndim != 2 or baseline.shape != event.shape:
        raise InundationError("baseline_water and event_water must be same-sized 2-D masks.")
    if not np.isfinite(pixel_area_m2) or pixel_area_m2 <= 0:
        raise InundationError("pixel_area_m2 must be a positive finite number.")

    common = np.ones(baseline.shape, dtype=bool)
    if baseline_valid is not None:
        mask = np.asarray(baseline_valid, dtype=bool)
        if mask.shape != baseline.shape:
            raise InundationError("baseline_valid shape must match water masks.")
        common &= mask
    if event_valid is not None:
        mask = np.asarray(event_valid, dtype=bool)
        if mask.shape != baseline.shape:
            raise InundationError("event_valid shape must match water masks.")
        common &= mask

    base_count = int(np.count_nonzero(baseline & common))
    event_count = int(np.count_nonzero(event & common))
    new_mask = event & ~baseline & common
    new_count = int(new_mask.sum())
    factor = float(pixel_area_m2) / 1_000_000.0
    base_area = base_count * factor
    event_area = event_count * factor
    new_area = new_count * factor
    change = ((event_area - base_area) / base_area * 100.0) if base_area > 0 else None

    return InundationResult(
        newly_inundated_mask=new_mask,
        common_valid_mask=common,
        baseline_water_area_km2=base_area,
        event_water_area_km2=event_area,
        newly_inundated_area_km2=new_area,
        water_area_change_percent=change,
        valid_pixel_count=int(common.sum()),
    )
