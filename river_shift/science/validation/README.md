# Scientific validation and evidence contract

## Purpose

Every RiverShift numerical output must be traceable, reproducible and independently checkable. This folder supplies metrics for comparing a predicted binary map with an independently prepared reference label.

## Required reference data

A validation run must record:
- Reference source and URL/provider.
- Reference acquisition/observation date.
- Interpreter or method used to create labels.
- Spatial resolution and coordinate reference system.
- Sampling design and class balance.
- Valid/no-data mask and any exclusion rules.

Do not use the same classifier output as both prediction and reference truth.

## Metrics

For a binary water/open-water task:
- True positive (TP): predicted water and reference water.
- False positive (FP): predicted water and reference non-water.
- False negative (FN): predicted non-water and reference water.
- True negative (TN): predicted non-water and reference non-water.

Reported measures:
- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)
- F1 = harmonic mean of precision and recall.
- IoU = TP / (TP + FP + FN)
- Overall accuracy = (TP + TN) / all valid samples.

Undefined ratios are returned as null, not silently converted to zero.

## Required validation before public claims

1. Use independent reference labels.
2. Report confusion matrix and metrics.
3. Assess water threshold sensitivity.
4. Inspect false positives/false negatives in flooded vegetation, shadow, wet soil, urban surfaces and smooth bare ground.
5. Check spatial sampling bias and class imbalance.
6. Publish sample count, dates, resolution and known limitations.

## Important distinction

Software unit tests prove that code follows its mathematical contract on controlled inputs. They do not prove remote-sensing accuracy on the Jamuna River. Any reported accuracy must come from a documented real-scene validation experiment.
