# RiverShift test plan

The suite is split into software-contract tests and later real-data validation experiments.

## Current automated tests

- ASF catalogue request validation and result normalization using a mocked client.
- GCOV HDF5 path, dimensions, coordinate axes, projection and valid-pixel checks using a synthetic HDF5 fixture.
- Gamma0 power-to-dB conversion and Otsu/fixed threshold behaviour.
- Newly inundated area using a hand-calculated raster.
- Multi-date persistence rules for erosion/deposition candidates.
- Confusion matrix, precision, recall, F1, IoU and no-data handling.

## What these tests do not claim

All fixtures are synthetic. Passing tests do not imply the classifier is accurate on NISAR or on the Jamuna. Real-scene validation needs a separate reference-label package and a documented experiment.

## Run

```bash
python -m pip install -r river_shift/requirements-river-shift.txt
python -m pytest river_shift/tests -q
```
