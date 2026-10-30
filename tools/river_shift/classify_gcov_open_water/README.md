# Script: classify one NISAR GCOV scene for open-water candidates

## Purpose

A reproducible command-line wrapper around the RiverShift GCOV reader, open-water candidate classifier and GeoTIFF exporter.

## Usage

From the repository root, after installing `Backend/requirements-river-shift.txt`:

```bash
python tools/river_shift/classify_gcov_open_water/run.py \
  --input /path/to/NISAR_GCOV_product.h5 \
  --output outputs/jamuna_scene_open_water.tif \
  --frequency A \
  --term VVVV \
  --method otsu
```

For a locally calibrated fixed threshold:

```bash
python tools/river_shift/classify_gcov_open_water/run.py \
  --input /path/to/NISAR_GCOV_product.h5 \
  --output outputs/jamuna_scene_open_water.tif \
  --frequency A --term VVVV --method fixed --threshold-db -17
```

The fixed value above is only an example argument; it is not a recommended universal NISAR threshold.

## Outputs

- GeoTIFF: 0 = valid non-water, 1 = open-water candidate, 255 = no-data.
- JSON sidecar: source file, selected frequency/term, EPSG, pixel area, method, threshold, valid count, candidate count, candidate area and caution label.

## Validation / acceptance

- Reader must locate the requested diagonal GCOV covariance dataset and its grid metadata.
- The output uses source projection and coordinate-derived pixel spacing.
- The sidecar records the method and threshold.
- The output is labelled as a candidate, not a validated flood map.

## Limitations

One scene cannot establish flood expansion or persistent erosion. Use the inundation and morphology modules with temporally comparable observations for event-level analysis. The initial reader loads the selected GCOV layer into memory; large product processing will need AOI-windowed/chunked reading.
