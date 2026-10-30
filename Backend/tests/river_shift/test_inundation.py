import numpy as np
import pytest

from science_adapter.river_shift.flood.inundation import InundationError, calculate_inundation


def test_inundation_area_matches_hand_calculation():
    baseline = np.array([[1, 1, 0], [0, 0, 0]], dtype=bool)
    event = np.array([[1, 1, 1], [0, 1, 0]], dtype=bool)
    result = calculate_inundation(baseline, event, pixel_area_m2=10000)
    assert result.baseline_water_area_km2 == pytest.approx(0.02)
    assert result.event_water_area_km2 == pytest.approx(0.04)
    assert result.newly_inundated_area_km2 == pytest.approx(0.02)
    assert result.water_area_change_percent == pytest.approx(100.0)
    assert result.newly_inundated_mask.tolist() == [[False, False, True], [False, True, False]]


def test_invalid_pixels_are_excluded_from_all_area_totals():
    baseline = np.array([[1, 0], [0, 0]], dtype=bool)
    event = np.array([[1, 1], [0, 0]], dtype=bool)
    valid = np.array([[False, True], [True, True]])
    result = calculate_inundation(
        baseline, event, pixel_area_m2=10000,
        baseline_valid=valid, event_valid=valid,
    )
    assert result.baseline_water_area_km2 == 0
    assert result.newly_inundated_area_km2 == pytest.approx(0.01)
    assert result.water_area_change_percent is None


def test_mismatched_shapes_are_rejected():
    with pytest.raises(InundationError):
        calculate_inundation(np.ones((2, 2)), np.ones((3, 2)), pixel_area_m2=100)
