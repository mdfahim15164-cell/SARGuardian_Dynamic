import numpy as np
import pytest

from science_adapter.river_shift.flood.water_classification import (
    WaterClassificationError,
    classify_open_water,
    power_to_db,
)


def test_power_to_db_uses_ten_log10_and_masks_invalid():
    power = np.array([[1.0, 0.1], [0.01, 0.0]])
    result = power_to_db(power)
    assert result[0, 0] == pytest.approx(0.0)
    assert result[0, 1] == pytest.approx(-10.0)
    assert result[1, 0] == pytest.approx(-20.0)
    assert np.isnan(result[1, 1])


def test_fixed_threshold_classifies_low_returns_as_open_water_candidates():
    power = np.array([[0.001, 0.002], [0.2, 0.4]])
    result = classify_open_water(power, method="fixed", threshold_db=-15, minimum_valid_pixels=4)
    assert result.water_mask.tolist() == [[True, True], [False, False]]
    assert result.water_candidate_count == 2


def test_otsu_finds_separation_in_two_class_synthetic_data():
    low = np.full((10, 10), 0.001)
    high = np.full((10, 10), 0.2)
    power = np.concatenate([low, high], axis=1)
    result = classify_open_water(power, method="otsu", minimum_valid_pixels=100)
    assert -25 < result.threshold_db < -5
    assert result.water_candidate_count == 100


def test_external_validity_mask_is_enforced():
    power = np.full((10, 10), 0.01)
    valid = np.ones((10, 10), dtype=bool)
    valid[0, 0] = False
    result = classify_open_water(power, valid_mask=valid, method="fixed", threshold_db=-10)
    assert result.valid_pixel_count == 99
    assert not result.water_mask[0, 0]


def test_insufficient_valid_pixels_rejected():
    with pytest.raises(WaterClassificationError):
        classify_open_water(np.ones((4, 4)), minimum_valid_pixels=20)
