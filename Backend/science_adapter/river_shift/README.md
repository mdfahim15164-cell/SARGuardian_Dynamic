# RiverShift science package

Canonical implementation location for deployment from the existing `Backend/` project root.

## Modules

| Scientific task | Code | Task README |
|---|---|---|
| ASF NISAR GCOV catalogue discovery | `data_access/catalog.py` | `data_access/README.md` |
| NISAR GCOV HDF5 reader | `data_access/gcov_reader.py` | `data_access/README.md` |
| Open-water candidate classification | `flood/water_classification.py` | `flood/water_classification.README.md` |
| Event inundation accounting | `flood/inundation.py` | `flood/inundation.README.md` |
| Persistent erosion/deposition candidates | `morphology/persistent_change.py` | `morphology/persistent_change.README.md` |
| Confusion matrix and threshold sensitivity | `validation/metrics.py`, `validation/sensitivity.py` | `validation/README.md` |

Every method README is intentionally placed next to the scientific task so a reviewer or AI code-review assistant can understand the method before reading or evaluating the implementation.

## Install and test

From `Backend/`:

```bash
python -m pip install -r requirements-river-shift.txt
python -m pytest tests/river_shift -q
```

The tests use synthetic fixtures. They validate software behavior, not real-world NISAR mapping accuracy.

## Current limitation

This is the scientific foundation only. A production run still requires the separate GCOV download worker, comparable-scene stack selector, AOI clipping/export, real-scene reference data and independent validation report. Do not display synthetic test results as a real Jamuna event.
