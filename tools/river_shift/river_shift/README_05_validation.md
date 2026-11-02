# Scientific module 05 · Independent binary classification validation

## Role
Compute classification quality statistics against a separate reference water mask.

## Required provenance
- Reference data source.
- Reference observation date.
- Reference production method.
- Same CRS, dimensions and affine transform as the prediction.
- Binary coding: 1=water and 0=non-water.

## Metrics
- TP, TN, FP, FN
- accuracy
- precision (user's accuracy)
- recall (producer's accuracy)
- specificity
- F1 score
- intersection over union (IoU)
- Cohen's kappa
- water-area bias

## Equations
    Precision = TP / (TP + FP)
    Recall = TP / (TP + FN)
    F1 = 2 * Precision * Recall / (Precision + Recall)
    IoU = TP / (TP + FP + FN)

## Validation
Synthetic tests verify the confusion matrix and F1/IoU calculations and require reference provenance before a report is produced.

## Acceptance / AI review
- Reference source, date and method cannot be blank.
- Prediction and reference must be binary.
- NoData and grid mismatch are rejected or excluded as documented.
- Confusion matrix counts are retained.
- F1 and IoU are published with accuracy.
- The report warns that a Sentinel-2-derived mask is a reference source, not automatic ground truth.

## Limitations
A reference mask is not infallible. Cloud, shadow, temporal offset, water-index thresholds and manual digitization can introduce error. The CLI resamples spatial blocks with replacement and reports 95% percentile intervals when at least 20 valid blocks are available. These intervals describe block-to-block variation at the chosen block size; they exclude reference-label and systematic sensor errors. Fewer than 20 blocks yields an explicit no-interval status. Validation provenance is marked complete only when the prediction hash matches an output mask in the adjacent RiverShift result report and that report contains NISAR GCOV granule IDs/checksums. Metrics remain provisional until a human reviewer confirms reference independence and suitability.

## References
- Sentinel-2: https://dataspace.copernicus.eu/explore-data/data-collections/sentinel-data/sentinel-2
- Dynamic World: https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1
