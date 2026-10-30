"""Threshold sensitivity helper for the open-water baseline."""
from __future__ import annotations

import numpy as np

from ..flood.water_classification import classify_open_water
from .metrics import binary_confusion_metrics


def evaluate_fixed_thresholds(
    power: np.ndarray,
    reference_water: np.ndarray,
    thresholds_db: list[float],
    *,
    valid_mask: np.ndarray | None = None,
) -> list[dict[str, float | int | None]]:
    """Evaluate a declared list of fixed dB thresholds against independent labels."""
    rows: list[dict[str, float | int | None]] = []
    for threshold in thresholds_db:
        result = classify_open_water(
            power,
            valid_mask=valid_mask,
            method="fixed",
            threshold_db=float(threshold),
        )
        metrics = binary_confusion_metrics(
            result.water_mask,
            reference_water,
            valid_mask=result.valid_mask,
        )
        rows.append({
            "threshold_db": float(threshold),
            "water_candidate_count": result.water_candidate_count,
            "valid_pixel_count": result.valid_pixel_count,
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1": metrics["f1"],
            "iou": metrics["iou"],
            "accuracy": metrics["accuracy"],
        })
    return rows
