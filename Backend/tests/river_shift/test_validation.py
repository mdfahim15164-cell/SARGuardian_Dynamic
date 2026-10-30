import numpy as np
import pytest

from science_adapter.river_shift.validation.metrics import ValidationError, binary_confusion_metrics
from science_adapter.river_shift.validation.sensitivity import evaluate_fixed_thresholds


def test_binary_confusion_metrics():
    prediction = np.array([[1, 1], [0, 0]])
    reference = np.array([[1, 0], [1, 0]])
    result = binary_confusion_metrics(prediction, reference)
    assert (result["tp"], result["fp"], result["fn"], result["tn"]) == (1, 1, 1, 1)
    assert result["precision"] == pytest.approx(0.5)
    assert result["recall"] == pytest.approx(0.5)
    assert result["f1"] == pytest.approx(0.5)
    assert result["iou"] == pytest.approx(1 / 3)
    assert result["accuracy"] == pytest.approx(0.5)


def test_validation_ignores_declared_invalid_pixels():
    prediction = np.array([[1, 1], [0, 0]])
    reference = np.array([[1, 0], [1, 0]])
    valid = np.array([[1, 0], [1, 1]], dtype=bool)
    result = binary_confusion_metrics(prediction, reference, valid_mask=valid)
    assert result["sample_count"] == 3
    assert result["tp"] == 1 and result["fp"] == 0 and result["fn"] == 1


def test_invalid_non_binary_values_rejected():
    with pytest.raises(ValidationError):
        binary_confusion_metrics(np.array([[0, 2]]), np.array([[0, 1]]))


def test_threshold_sensitivity_returns_one_row_per_threshold():
    power = np.array([[0.001, 0.01], [0.2, 0.4]])
    truth = np.array([[1, 1], [0, 0]])
    rows = evaluate_fixed_thresholds(power, truth, [-15, -5], valid_mask=np.ones((2, 2), dtype=bool))
    assert len(rows) == 2
    assert all("f1" in row for row in rows)
