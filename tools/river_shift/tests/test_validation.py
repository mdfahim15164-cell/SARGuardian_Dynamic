import numpy as np

from river_shift.validation import validate_binary_classification


def test_validation_metrics_are_calculated_from_confusion_matrix(raster_writer):
    prediction = np.array([[1, 0], [1, 0]], dtype=np.uint8)
    reference = np.array([[1, 0], [0, 1]], dtype=np.uint8)
    pred_path = raster_writer("prediction.tif", prediction)
    ref_path = raster_writer("reference.tif", reference)
    result = validate_binary_classification(
        str(pred_path), str(ref_path), reference_source="independent test mask",
        reference_date="2026-07-01", reference_method="manually reviewed synthetic fixture",
    )
    assert result["confusion_matrix"] == {
        "true_positive": 1, "true_negative": 1, "false_positive": 1, "false_negative": 1
    }
    assert result["metrics"]["accuracy"] == 0.5
    assert result["metrics"]["f1_score"] == 0.5
    assert round(result["metrics"]["intersection_over_union"], 6) == round(1 / 3, 6)


def test_validation_requires_reference_provenance(raster_writer):
    values = np.array([[1, 0], [0, 1]], dtype=np.uint8)
    path = raster_writer("mask.tif", values)
    import pytest
    with pytest.raises(ValueError, match="reference_source"):
        validate_binary_classification(
            str(path), str(path), reference_source="", reference_date="2026-07-01",
            reference_method="manual",
        )
