from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

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


def run_flood_analysis(
    *,
    before_path: str,
    during_path: str,
    after_path: str,
    output_dir: str,
    units: str,
    threshold_db: float | None,
    use_otsu: bool,
    permanent_water_path: str | None = None,
    minimum_patch_hectares: float = 0.0,
    dates: dict[str, str] | None = None,
    maturity: str = "UNSPECIFIED",
    frequency: str = "frequencyA",
    polarization_term: str = "VVVV",
) -> dict[str, Any]:
    """Run three-date flood-water expansion screening on one co-registered GCOV layer."""
    arrays: dict[str, np.ndarray] = {}
    valids: dict[str, np.ndarray] = {}
    profiles: dict[str, dict[str, Any]] = {}
    for key, path in {
        "before": before_path,
        "during": during_path,
        "after": after_path,
    }.items():
        arrays[key], valids[key], profiles[key] = read_band(path)

    if permanent_water_path:
        arrays["permanent"], valids["permanent"], profiles["permanent"] = read_band(permanent_water_path)
    assert_same_grid(profiles)

    pixel_area_m2 = require_projected_metre_grid(profiles["before"])
    valid_common = valids["before"] & valids["during"] & valids["after"]

    db_arrays = {key: power_to_db(arrays[key], units) for key in ("before", "during", "after")}
    combined = np.concatenate(
        [db_arrays[key][valid_common] for key in ("before", "during", "after")]
    )
    combined_valid = np.isfinite(combined)
    if threshold_db is None:
        if not use_otsu:
            raise ValueError("Provide threshold_db or enable Otsu.")
        threshold_db = otsu_threshold_db(
            combined.reshape(1, -1),
            combined_valid.reshape(1, -1),
        )
        threshold_method = "otsu_combined_three_dates_exploratory"
    else:
        threshold_method = "fixed_user_supplied_db_threshold"

    min_pixels = int(np.ceil((minimum_patch_hectares * 10_000.0) / pixel_area_m2))
    water = {
        key: classify_open_water(
            arrays[key],
            valids[key],
            units=units,
            threshold_db=threshold_db,
            minimum_pixels=min_pixels,
        )
        for key in ("before", "during", "after")
    }

    comparison_valid = valid_common.copy()
    new_water = water["during"] & ~water["before"] & comparison_valid

    permanent_excluded = False
    if permanent_water_path:
        permanent_mask = valids["permanent"] & (arrays["permanent"] > 0)
        new_water &= ~permanent_mask
        permanent_excluded = True

    baseline_area = float(water["before"][valid_common].sum() * pixel_area_m2 / 1_000_000)
    peak_area = float(water["during"][valid_common].sum() * pixel_area_m2 / 1_000_000)
    post_area = float(water["after"][valid_common].sum() * pixel_area_m2 / 1_000_000)
    new_area = float(new_water.sum() * pixel_area_m2 / 1_000_000)
    change_percent = (
        ((peak_area - baseline_area) / baseline_area) * 100.0
        if baseline_area > 0
        else None
    )

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for key in ("before", "during", "after"):
        write_mask(out / f"{key}_water_mask.tif", water[key], valids[key], profiles[key])
    write_mask(out / "newly_water_covered_mask.tif", new_water, comparison_valid, profiles["before"])
    polygon_count = write_mask_geojson(
        out / "newly_water_covered.geojson",
        new_water,
        comparison_valid,
        profiles["before"],
        class_name="newly_water_covered",
    )

    result: dict[str, Any] = {
        "schema_version": 1,
        "engine": "RiverShift",
        "analysis_type": "flood_inundation_screening",
        "source": {
            "mission": "NISAR",
            "instrument": "L-SAR",
            "product": "GCOV",
            "maturity": maturity.upper(),
            "frequency": frequency,
            "covariance_term": polarization_term,
            "quantity": "gamma0_power_or_declared_input_units",
        },
        "inputs": {
            "before": str(before_path),
            "during": str(during_path),
            "after": str(after_path),
            "permanent_water_mask": str(permanent_water_path) if permanent_water_path else None,
            "dates": dates or {},
            "input_units": units,
        },
        "method": {
            "classification": "low_backscatter_open_water_candidate",
            "threshold_db": safe_float(threshold_db),
            "threshold_method": threshold_method,
            "minimum_patch_hectares": float(minimum_patch_hectares),
            "permanent_water_excluded": permanent_excluded,
        },
        "metrics": {
            "baseline_water_area_km2": baseline_area,
            "peak_water_area_km2": peak_area,
            "post_event_water_area_km2": post_area,
            "newly_water_covered_area_km2": new_area,
            "water_area_change_percent": safe_float(change_percent),
            "new_water_polygon_count": int(polygon_count),
        },
        "quality": {
            "status": "SCREENING_NOT_INDEPENDENTLY_VALIDATED",
            "valid_comparison_pixel_count": int(comparison_valid.sum()),
            "permanent_water_filter_applied": permanent_excluded,
            "warnings": [
                "New water coverage relative to the pre-event observation is not automatically proof of floodplain inundation.",
                "Use comparable orbit geometry, acquisition mode, frequency, polarization, maturity and hydrological conditions.",
                "Low-backscatter screening may miss inundated vegetation because double-bounce scattering can be bright.",
                "Validate the water mask against independent reference data before reporting accuracy or impact claims.",
            ],
        },
        "outputs": {
            "before_water_mask": "before_water_mask.tif",
            "during_water_mask": "during_water_mask.tif",
            "after_water_mask": "after_water_mask.tif",
            "new_water_mask": "newly_water_covered_mask.tif",
            "new_water_geojson": "newly_water_covered.geojson",
        },
    }
    save_json(out / "river_shift_result.json", result)
    return result
