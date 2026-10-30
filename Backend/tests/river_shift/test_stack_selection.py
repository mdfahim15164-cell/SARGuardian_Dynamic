from science_adapter.river_shift.data_access.stack_selection import select_comparable_gcov_stack


def _scene(name, *, relative_orbit="029", crid="P05000", maturity="PROVISIONAL"):
    return {
        "granule_name": name,
        "data_maturity": maturity,
        "identity": {
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
