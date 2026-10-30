from science_adapter.river_shift.data_access.stack_selection import select_comparable_gcov_stack


def _scene(name, *, relative_orbit="029", crid="P05000", maturity="PROVISIONAL"):
    return {
        "granule_name": name,
        "data_maturity": maturity,
        "identity": {
            "instrument_band": "L", "processing_level": "L2",
            "processing_type": "PR", "cycle_number": name[-3:],
            "relative_orbit": relative_orbit, "flight_direction": "ASCENDING",
            "frame_number": "010", "acquisition_mode": "0005",
            "polarization_mode": "NASV", "source_mode": "A", "crid": crid,
        },
        "start_time": name,
    }


def test_stack_selector_groups_same_track_and_crid_across_cycles():
    scenes = [
        _scene("scene-001"),
        _scene("scene-002"),
        _scene("scene-003"),
        _scene("scene-other-track", relative_orbit="030"),
        _scene("scene-other-crid", crid="P05001"),
    ]
    result = select_comparable_gcov_stack(scenes, requested_maturity="PROVISIONAL")
    assert result["status"] == "ready_for_hdf5_grid_checks"
    assert result["eligible_count"] == 3
    assert len(result["cycle_numbers"]) == 3
    assert len(result["excluded_scenes"]) == 2


def test_stack_selector_rejects_mixed_maturity():
    scenes = [
        _scene("scene-001"),
        _scene("scene-002"),
        _scene("scene-003", maturity="BETA"),
    ]
    result = select_comparable_gcov_stack(scenes, requested_maturity="PROVISIONAL")
    assert result["eligible_count"] == 2
    assert result["status"] == "insufficient_data"


def test_stack_selector_requires_complete_metadata():
    scene = {"granule_name": "unknown.h5", "catalogue_maturity_filter": "PROVISIONAL"}
    result = select_comparable_gcov_stack([scene, scene], requested_maturity="PROVISIONAL")
    assert result["eligible_count"] == 0
    assert result["status"] == "insufficient_data"


def test_stack_selector_does_not_mix_l_band_and_s_band():
    scenes = [
        _scene("scene-L-1"),
        _scene("scene-L-2"),
        _scene("scene-S-3"),
    ]
    scenes[2]["identity"]["instrument_band"] = "S"
    scenes[2]["identity"]["processing_level"] = "S2"
    result = select_comparable_gcov_stack(scenes, requested_maturity="PROVISIONAL")
    assert result["eligible_count"] == 2
    assert result["comparison_key"]["instrument_band"] == "L"
    assert len(result["excluded_scenes"]) == 1


def _raster(*, x_shift=0.0, term="VVVV"):
    import numpy as np
    from pyproj import CRS
    from science_adapter.river_shift.data_access.gcov_reader import GcovRaster

    return GcovRaster(
        power=np.ones((2, 3), dtype=np.float32),
        valid_mask=np.ones((2, 3), dtype=bool),
        x_coordinates=np.array([500005.0, 500015.0, 500025.0]) + x_shift,
        y_coordinates=np.array([2800005.0, 2799995.0]),
        crs_wkt=CRS.from_epsg(32646).to_wkt(),
        epsg=32646,
        frequency="A",
        covariance_term=term,
        source_path="synthetic.h5",
        units="linear gamma0 power",
    )


def test_grid_validator_accepts_exact_same_grid():
    from science_adapter.river_shift.data_access.stack_selection import validate_gcov_grid_stack

    result = validate_gcov_grid_stack([_raster(), _raster()])
    assert result["status"] == "grid_compatible"
    assert result["pixel_area_m2"] == 100.0


def test_grid_validator_rejects_shifted_origin_and_different_term():
    import pytest
    from science_adapter.river_shift.data_access.stack_selection import (
        StackCompatibilityError,
        validate_gcov_grid_stack,
    )

    with pytest.raises(StackCompatibilityError, match="xCoordinates"):
        validate_gcov_grid_stack([_raster(), _raster(x_shift=10.0)])
    with pytest.raises(StackCompatibilityError, match="covariance term"):
        validate_gcov_grid_stack([_raster(), _raster(term="HHHH")])
