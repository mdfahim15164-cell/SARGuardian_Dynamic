import numpy as np
import pytest

from science_adapter.river_shift.morphology.persistent_change import (
    PersistentChangeError,
    detect_persistent_change,
)


def test_persistent_erosion_and_deposition_candidates():
    before = np.array([[0, 1], [0, 1]], dtype=bool)
    post = np.array([
        [[1, 0], [0, 0]],
        [[1, 0], [0, 0]],
        [[1, 0], [0, 0]],
    ], dtype=bool)
    result = detect_persistent_change(
        before, post, pixel_area_m2=10000,
        persistence_fraction=0.8, minimum_post_observations=2,
    )
    assert result.erosion_candidate_mask.tolist() == [[True, False], [False, False]]
    assert result.deposition_candidate_mask.tolist() == [[False, True], [False, True]]
    assert result.erosion_candidate_area_ha == pytest.approx(1.0)
    assert result.deposition_candidate_area_ha == pytest.approx(2.0)
    assert result.net_candidate_land_gain_ha == pytest.approx(1.0)


def test_missing_post_observations_does_not_confirm_change():
    before = np.array([[0]], dtype=bool)
    post = np.array([[[1]], [[1]]], dtype=bool)
    valid = np.array([[[1]], [[0]]], dtype=bool)
    result = detect_persistent_change(
        before, post, pixel_area_m2=10000, post_valid_stack=valid,
        minimum_post_observations=2,
    )
    assert not result.erosion_candidate_mask[0, 0]
    assert np.isnan(result.post_water_fraction[0, 0])


def test_persistence_fraction_must_be_majority():
    with pytest.raises(PersistentChangeError):
        detect_persistent_change(
            np.zeros((1, 1)), np.zeros((2, 1, 1)), pixel_area_m2=100,
            persistence_fraction=0.5,
        )
