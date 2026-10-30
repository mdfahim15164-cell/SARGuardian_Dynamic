from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .raster_io import assert_same_grid, read_band, require_projected_metre_grid, save_json, safe_float


def validate_binary_classification(
    prediction_path: str,
    reference_path: str,
    *,
    reference_source: str,
    reference_date: str,
    reference_method: str,
) -> dict[str, Any]:
    """Calculate confusion-matrix metrics against an independent binary reference mask."""
    for label, value in {
        "reference_source": reference_source,
        "reference_date": reference_date,
        "reference_method": reference_method,
    }.items():
        if not value.strip():
            raise ValueError(f"{label} is required for a reproducible validation report.")

    prediction, prediction_valid, prediction_profile = read_band(prediction_path)
    reference, reference_valid, reference_profile = read_band(reference_path)
    assert_same_grid({"prediction": prediction_profile, "reference": reference_profile})
    pixel_area_m2 = require_projected_metre_grid(prediction_profile)

    valid = prediction_valid & reference_valid
    pred_values = prediction[valid]
    ref_values = reference[valid]
    if pred_values.size == 0:
        raise ValueError("No overlapping valid pixels are available for validation.")
    if not np.isin(pred_values, [0, 1]).all():
        raise ValueError("Prediction raster must be binary: 0=non-water, 1=water.")
    if not np.isin(ref_values, [0, 1]).all():
        raise ValueError("Reference raster must be binary: 0=non-water, 1=water.")

    pred = pred_values.astype(bool)
    ref = ref_values.astype(bool)
    tp = int(np.sum(pred & ref))
    tn = int(np.sum(~pred & ~ref))
    fp = int(np.sum(pred & ~ref))
    fn = int(np.sum(~pred & ref))
    total = tp + tn + fp + fn

    accuracy = (tp + tn) / total
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    iou = tp / (tp + fp + fn) if tp + fp + fn else 0.0

    expected = (
        ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn))
        / (total * total)
    )
    observed = accuracy
    kappa = (observed - expected) / (1 - expected) if expected < 1 else None
    area_bias_percent = (
        ((int(pred.sum()) - int(ref.sum())) / int(ref.sum())) * 100
        if int(ref.sum()) > 0
        else None
    )

    return {
        "schema_version": 1,
        "engine": "RiverShift",
        "analysis_type": "classification_validation",
        "source": {"prediction": str(prediction_path), "reference": str(reference_path)},
        "reference": {
            "source": reference_source,
            "date": reference_date,
            "method": reference_method,
            "independent_reference_required": True,
        },
        "confusion_matrix": {"true_positive": tp, "true_negative": tn, "false_positive": fp, "false_negative": fn},
        "metrics": {
            "valid_pixel_count": total,
            "accuracy": safe_float(accuracy),
            "precision_user_accuracy": safe_float(precision),
            "recall_producer_accuracy": safe_float(recall),
            "specificity": safe_float(specificity),
            "f1_score": safe_float(f1),
            "intersection_over_union": safe_float(iou),
            "cohen_kappa": safe_float(kappa),
            "area_bias_percent": safe_float(area_bias_percent),
            "prediction_water_area_km2": float(pred.sum() * pixel_area_m2 / 1_000_000),
            "reference_water_area_km2": float(ref.sum() * pixel_area_m2 / 1_000_000),
        },
        "quality": {
            "status": "VALIDATED_AGAINST_DECLARED_REFERENCE",
            "warnings": [
                "Validation quality is only as strong as the independence and positional accuracy of the reference mask.",
                "A cloud-free Sentinel-2-derived mask is a reference source, not automatically ground truth; document its date, cloud filtering and classification method.",
                "Report class imbalance and the confusion matrix alongside aggregate accuracy.",
            ],
        },
    }


def save_validation_report(result: dict[str, Any], output_path: str | Path) -> None:
    save_json(output_path, result)
