"""Multi-date persistent land/water transition candidates."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


class PersistentChangeError(ValueError):
    """Raised for invalid or incompatible morphology inputs."""


@dataclass(frozen=True)
class PersistentChangeResult:
    erosion_candidate_mask: np.ndarray
    deposition_candidate_mask: np.ndarray
    post_water_fraction: np.ndarray
    post_valid_observation_count: np.ndarray
    erosion_candidate_area_ha: float
    deposition_candidate_area_ha: float
    net_candidate_land_gain_ha: float


def detect_persistent_change(
    before_water: np.ndarray,
    post_water_stack: np.ndarray,
    *,
    pixel_area_m2: float,
    post_valid_stack: np.ndarray | None = None,
    before_valid: np.ndarray | None = None,
    persistence_fraction: float = 0.8,
    minimum_post_observations: int = 2,
) -> PersistentChangeResult:
    """Find persistent post-event water/land transitions on one common grid."""
    before = np.asarray(before_water, dtype=bool)
    stack = np.asarray(post_water_stack, dtype=bool)
    if before.ndim != 2 or stack.ndim != 3 or stack.shape[1:] != before.shape:
        raise PersistentChangeError("Expected before_water[y,x] and post_water_stack[time,y,x] with matching grids.")
    if stack.shape[0] < minimum_post_observations or minimum_post_observations < 1:
        raise PersistentChangeError("Not enough post-event observations for the requested persistence test.")
    if not np.isfinite(pixel_area_m2) or pixel_area_m2 <= 0:
        raise PersistentChangeError("pixel_area_m2 must be positive and finite.")
    if not 0.5 < persistence_fraction <= 1.0:
        raise PersistentChangeError("persistence_fraction must be in (0.5, 1.0].")

    if post_valid_stack is None:
        valid_stack = np.ones(stack.shape, dtype=bool)
    else:
        valid_stack = np.asarray(post_valid_stack, dtype=bool)
        if valid_stack.shape != stack.shape:
            raise PersistentChangeError("post_valid_stack must match post_water_stack shape.")

    valid_count = valid_stack.sum(axis=0)
    water_count = (stack & valid_stack).sum(axis=0)
    fraction = np.full(before.shape, np.nan, dtype=np.float32)
    has_enough = valid_count >= minimum_post_observations
    fraction[has_enough] = water_count[has_enough] / valid_count[has_enough]

    if before_valid is None:
        before_is_valid = np.ones(before.shape, dtype=bool)
    else:
        before_is_valid = np.asarray(before_valid, dtype=bool)
        if before_is_valid.shape != before.shape:
            raise PersistentChangeError("before_valid must match before_water shape.")

    persistent_water = has_enough & (fraction >= persistence_fraction) & before_is_valid
    persistent_dry = has_enough & (fraction <= (1.0 - persistence_fraction)) & before_is_valid
    erosion = ~before & persistent_water
    deposition = before & persistent_dry

    area_ha = float(pixel_area_m2) / 10_000.0
    erosion_area = float(erosion.sum()) * area_ha
    deposition_area = float(deposition.sum()) * area_ha
    return PersistentChangeResult(
        erosion_candidate_mask=erosion,
        deposition_candidate_mask=deposition,
        post_water_fraction=fraction,
        post_valid_observation_count=valid_count.astype(np.uint16),
        erosion_candidate_area_ha=erosion_area,
        deposition_candidate_area_ha=deposition_area,
        net_candidate_land_gain_ha=deposition_area - erosion_area,
    )
