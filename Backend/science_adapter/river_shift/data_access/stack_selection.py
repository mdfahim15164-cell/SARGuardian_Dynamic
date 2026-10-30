"""Scientific comparability gates for multi-date NISAR GCOV stacks."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np
from pyproj import CRS

from .gcov_reader import GcovRaster
from .scene_identity import parse_gcov_granule_identity


class StackCompatibilityError(ValueError):
    """Raised when a set of rasters cannot be compared pixel by pixel."""


STACK_IDENTITY_FIELDS = (
    "instrument_band", "processing_level", "processing_type", "relative_orbit", "flight_direction", "frame_number",
    "acquisition_mode", "polarization_mode", "source_mode", "crid",
)


def _identity_for_scene(scene: dict[str, Any]) -> dict[str, Any] | None:
    existing = scene.get("identity")
    if isinstance(existing, dict):
        return existing
    return parse_gcov_granule_identity(str(scene.get("granule_name", "")))


def select_comparable_gcov_stack(
    scenes: list[dict[str, Any]],
    *,
    requested_maturity: str,
    minimum_scenes: int = 3,
) -> dict[str, Any]:
    """Return the largest compatible identity group; do not mix processing baselines."""
    maturity = requested_maturity.upper().strip()
    if maturity not in {"PROVISIONAL", "BETA"}:
        raise StackCompatibilityError("requested_maturity must be PROVISIONAL or BETA.")
    if not isinstance(minimum_scenes, int) or minimum_scenes < 2:
        raise StackCompatibilityError("minimum_scenes must be an integer of at least 2.")

    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    excluded: list[dict[str, str]] = []
    for scene in scenes:
        granule = str(scene.get("granule_name") or "unknown")
        effective_maturity = scene.get("data_maturity") or scene.get("catalogue_maturity_filter")
        if effective_maturity != maturity:
            excluded.append({"granule_name": granule, "reason": "maturity_missing_or_mismatched"})
            continue
        identity = _identity_for_scene(scene)
        if not identity:
            excluded.append({"granule_name": granule, "reason": "granule_identity_unparseable"})
            continue
        missing = [field for field in STACK_IDENTITY_FIELDS if identity.get(field) in (None, "")]
        if missing:
            excluded.append({"granule_name": granule, "reason": "missing_identity_fields:" + ",".join(missing)})
            continue
        key = (effective_maturity, *(identity[field] for field in STACK_IDENTITY_FIELDS))
        row = dict(scene)
        row["identity"] = identity
        row["effective_maturity"] = effective_maturity
        groups[key].append(row)

    if not groups:
        return {
            "status": "insufficient_data", "requested_maturity": maturity,
            "eligible_count": 0, "minimum_required": minimum_scenes,
            "eligible_scenes": [], "excluded_scenes": excluded,
            "comparison_key": None, "cycle_numbers": [],
            "warnings": ["No scenes had sufficient, compatible product identity metadata."],
        }

    selected_key, selected = max(groups.items(), key=lambda item: len(item[1]))
    selected.sort(key=lambda scene: scene.get("start_time") or scene["identity"]["start_time_utc"])
    selected_names = {scene["granule_name"] for scene in selected}
    for group in groups.values():
        for scene in group:
            if scene["granule_name"] not in selected_names:
                excluded.append({
                    "granule_name": scene["granule_name"],
                    "reason": "different_track_frame_mode_polarization_or_crid",
                })

    comparison = dict(zip(("maturity", *STACK_IDENTITY_FIELDS), selected_key))
    cycles = sorted({scene["identity"]["cycle_number"] for scene in selected})
    ready = len(selected) >= minimum_scenes
    return {
        "status": "ready_for_hdf5_grid_checks" if ready else "insufficient_data",
        "requested_maturity": maturity,
        "eligible_count": len(selected),
        "minimum_required": minimum_scenes,
        "eligible_scenes": selected,
        "excluded_scenes": excluded,
        "comparison_key": comparison,
        "cycle_numbers": cycles,
        "warnings": [
            "Passing metadata selection does not prove that raster grids align.",
            "Frequency and covariance-term availability must be verified inside each downloaded HDF5 product.",
            "This selector performs no water classification or area calculation.",
        ],
    }


def validate_gcov_grid_stack(rasters: list[GcovRaster]) -> dict[str, Any]:
    """Require matching frequency, term, CRS, shape and x/y coordinates."""
    if len(rasters) < 2:
        raise StackCompatibilityError("At least two GCOV rasters are required.")
    first = rasters[0]
    first_crs = CRS.from_wkt(first.crs_wkt)
    for index, raster in enumerate(rasters[1:], start=2):
        if raster.frequency != first.frequency:
            raise StackCompatibilityError(f"Raster {index} uses a different frequency band.")
        if raster.covariance_term != first.covariance_term:
            raise StackCompatibilityError(f"Raster {index} uses a different covariance term.")
        if raster.shape != first.shape:
            raise StackCompatibilityError(f"Raster {index} has a different raster shape.")
        if not first_crs.equals(CRS.from_wkt(raster.crs_wkt)):
            raise StackCompatibilityError(f"Raster {index} uses a different CRS.")
        if not np.allclose(raster.x_coordinates, first.x_coordinates, rtol=0, atol=1e-5):
            raise StackCompatibilityError(f"Raster {index} xCoordinates do not match.")
        if not np.allclose(raster.y_coordinates, first.y_coordinates, rtol=0, atol=1e-5):
            raise StackCompatibilityError(f"Raster {index} yCoordinates do not match.")
    return {
        "status": "grid_compatible",
        "scene_count": len(rasters),
        "shape_yx": list(first.shape),
        "epsg": first.epsg,
        "crs_wkt": first.crs_wkt,
        "frequency": first.frequency,
        "covariance_term": first.covariance_term,
        "pixel_area_m2": first.pixel_area_m2,
        "grid_alignment": "exact_coordinate_match",
    }
