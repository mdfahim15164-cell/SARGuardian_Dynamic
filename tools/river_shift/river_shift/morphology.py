from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from scipy import ndimage

from .raster_io import (
    assert_same_grid,
    power_to_db,
    read_band,
    require_projected_metre_grid,
    safe_float,
    save_json,
    write_mask,
    write_mask_geojson,
)
from .water_detection import classify_open_water, otsu_threshold_db


def _boundary(mask: np.ndarray) -> np.ndarray:
    return np.asarray(mask, dtype=bool) ^ ndimage.binary_erosion(
        np.asarray(mask, dtype=bool), structure=np.ones((3, 3), dtype=bool), border_value=0
    )


def symmetric_boundary_distance_m(
    before_water: np.ndarray,
    after_water: np.ndarray,
    *,
    pixel_size_y_m: float,
    pixel_size_x_m: float,
) -> tuple[float | None, float | None]:
    """Return symmetric mean and 95th-percentile distance between water boundaries.

    This is a boundary-change screening proxy, not a signed transect-based bank
    retreat/accretion rate. Complex braided channels may have multiple nearby banks.
    """
    before_edge = _boundary(before_water)
    after_edge = _boundary(after_water)
    if not before_edge.any() or not after_edge.any():
        return None, None

    distance_to_after = ndimage.distance_transform_edt(~after_edge, sampling=(pixel_size_y_m, pixel_size_x_m))
    distance_to_before = ndimage.distance_transform_edt(~before_edge, sampling=(pixel_size_y_m, pixel_size_x_m))
    distances = np.concatenate(
        [distance_to_after[before_edge], distance_to_before[after_edge]]
    )
    distances = distances[np.isfinite(distances)]
    if distances.size == 0:
        return None, None
    return float(np.mean(distances)), float(np.percentile(distances, 95))


def run_morphology_analysis(
    *,
    before_path: str,
    post_one_path: str,
    post_two_path: str,
    output_dir: str,
    units: str,
    threshold_db: float | None,
    use_otsu: bool,
    dates: dict[str, str] | None = None,
    maturity: str = "UNSPECIFIED",
    frequency: str = "frequencyA",
    polarization_term: str = "VVVV",
) -> dict[str, Any]:
    """Screen persistent post-event water/land transitions for erosion/deposition candidates."""
    paths = {
        "before": before_path,
        "post_one": post_one_path,
        "post_two": post_two_path,
    }
    arrays: dict[str, np.ndarray] = {}
    valids: dict[str, np.ndarray] = {}
    profiles: dict[str, dict[str, Any]] = {}
    for key, path in paths.items():
        arrays[key], valids[key], profiles[key] = read_band(path)
    assert_same_grid(profiles)

    pixel_area_m2 = require_projected_metre_grid(profiles["before"])
    valid = valids["before"] & valids["post_one"] & valids["post_two"]
    db_arrays = {key: power_to_db(arrays[key], units) for key in paths}
    combined = np.concatenate([db_arrays[key][valid] for key in paths])
    combined_valid = np.isfinite(combined)
    if threshold_db is None:
        if not use_otsu:
            raise ValueError("Provide threshold_db or enable Otsu.")
        threshold_db = otsu_threshold_db(combined.reshape(1, -1), combined_valid.reshape(1, -1))
        threshold_method = "otsu_combined_three_dates_exploratory"
    else:
        threshold_method = "fixed_user_supplied_db_threshold"

    water = {
        key: classify_open_water(
            arrays[key], valids[key], units=units, threshold_db=threshold_db
        )
        for key in paths
    }

    stable_post_water = water["post_one"] & water["post_two"] & valid
    stable_post_land = ~water["post_one"] & ~water["post_two"] & valid

    erosion_candidate = ~water["before"] & stable_post_water & valid
    deposition_candidate = water["before"] & stable_post_land & valid

    erosion_area = float(erosion_candidate.sum() * pixel_area_m2 / 10_000)
    deposition_area = float(deposition_candidate.sum() * pixel_area_m2 / 10_000)
    net_land_change = deposition_area - erosion_area

    transform = profiles["before"]["transform"]
    mean_shift, p95_shift = symmetric_boundary_distance_m(
        water["before"],
        stable_post_water,
        pixel_size_y_m=abs(float(transform.e)),
        pixel_size_x_m=abs(float(transform.a)),
    )

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_mask(out / "erosion_candidate_mask.tif", erosion_candidate, valid, profiles["before"])
    write_mask(out / "deposition_candidate_mask.tif", deposition_candidate, valid, profiles["before"])
    erosion_polygons = write_mask_geojson(
        out / "erosion_candidates.geojson",
        erosion_candidate,
        valid,
        profiles["before"],
        class_name="erosion_candidate",
    )
    deposition_polygons = write_mask_geojson(
        out / "deposition_candidates.geojson",
        deposition_candidate,
        valid,
        profiles["before"],
        class_name="deposition_candidate",
    )

    result: dict[str, Any] = {
        "schema_version": 1,
        "engine": "RiverShift",
        "analysis_type": "river_morphology_screening",
        "source": {
            "mission": "NISAR",
            "instrument": "L-SAR",
            "product": "GCOV",
            "maturity": maturity.upper(),
            "frequency": frequency,
            "covariance_term": polarization_term,
        },
        "inputs": {**paths, "dates": dates or {}, "input_units": units},
        "method": {
            "classification": "persistent_two_post_observation_water_land_transition",
            "threshold_db": safe_float(threshold_db),
            "threshold_method": threshold_method,
            "post_observations_required": 2,
        },
        "metrics": {
            "persistent_erosion_candidate_area_ha": erosion_area,
            "persistent_deposition_candidate_area_ha": deposition_area,
            "net_candidate_land_change_ha": net_land_change,
            "symmetric_boundary_distance_mean_m": safe_float(mean_shift),
            "symmetric_boundary_distance_p95_m": safe_float(p95_shift),
            "erosion_polygon_count": int(erosion_polygons),
            "deposition_polygon_count": int(deposition_polygons),
        },
        "quality": {
            "status": "PERSISTENCE_SCREENED_NOT_INDEPENDENTLY_VALIDATED",
            "valid_comparison_pixel_count": int(valid.sum()),
            "warnings": [
                "Land-to-water and water-to-land transitions are candidate erosion/deposition zones, not confirmed geomorphic causation.",
                "Two post-event observations reduce transient-water confusion but do not replace same-stage hydrological comparison or field validation.",
                "Boundary distance is a symmetric displacement proxy, not a signed transect-derived bank migration rate.",
                "For braided rivers, interpret outer active-channel belt and individual threads separately.",
                "Check for bank protection, dredging, sand mining, embankments and seasonal channel stage before attributing change to the flood.",
            ],
        },
        "outputs": {
            "erosion_mask": "erosion_candidate_mask.tif",
            "deposition_mask": "deposition_candidate_mask.tif",
            "erosion_geojson": "erosion_candidates.geojson",
            "deposition_geojson": "deposition_candidates.geojson",
        },
    }
    save_json(out / "river_shift_result.json", result)
    return result
