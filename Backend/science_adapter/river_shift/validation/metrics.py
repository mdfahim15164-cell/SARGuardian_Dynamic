"""Independent-reference validation metrics for binary raster classifications."""
from __future__ import annotations

import numpy as np


class ValidationError(ValueError):
    """Raised for invalid prediction/reference arrays."""


def binary_confusion_metrics(
    prediction: np.ndarray,
    reference: np.ndarray,
    *,
    valid_mask: np.ndarray | None = None,
) -> dict[str, int | float | None]:
    """Return TP/FP/FN/TN, precision, recall, F1, IoU and accuracy."""
    pred = np.asarray(prediction)
    truth = np.asarray(reference)
    if pred.ndim != 2 or truth.ndim != 2 or pred.shape != truth.shape:
        raise ValidationError("prediction and reference must be same-sized 2-D arrays.")
    if not np.isin(pred, [0, 1, False, True]).all() or not np.isin(truth, [0, 1, False, True]).all():
        raise ValidationError("prediction and reference must contain only binary 0/1 values.")

    valid = np.ones(pred.shape, dtype=bool)
    if valid_mask is not None:
        mask = np.asarray(valid_mask)
        if mask.shape != pred.shape:
            raise ValidationError("valid_mask must match prediction shape.")
        if mask.dtype != np.bool_:
            if (
                not np.issubdtype(mask.dtype, np.number)
                or not np.isfinite(mask).all()
                or not np.isin(mask, [0, 1]).all()
            ):
                raise ValidationError("valid_mask must contain only Boolean or finite 0/1 values.")
        valid &= mask.astype(bool)

    p = pred.astype(bool)[valid]
    t = truth.astype(bool)[valid]
    tp = int(np.count_nonzero(p & t))
    fp = int(np.count_nonzero(p & ~t))
    fn = int(np.count_nonzero(~p & t))
    tn = int(np.count_nonzero(~p & ~t))
    total = tp + fp + fn + tn

    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall > 0
        else (0.0 if precision == 0 and recall == 0 else None)
    )
    iou = tp / (tp + fp + fn) if tp + fp + fn else None
    accuracy = (tp + tn) / total if total else None
    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "sample_count": total,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "iou": iou,
        "accuracy": accuracy,
    }
