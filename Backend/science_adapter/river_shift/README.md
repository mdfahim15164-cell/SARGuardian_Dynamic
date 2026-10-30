# RiverShift science package

Canonical implementation location for deployment from the existing Backend project root.

## Scientific task index

| Task | Implementation | Explanation / validation README |
|---|---|---|
| ASF NISAR GCOV catalogue discovery | data_access/catalog.py | data_access/README.md |
| Scene identity and provenance | data_access/scene_identity.py | data_access/scene_identity.README.md |
| Comparable-scene and exact-grid gate | data_access/stack_selection.py | data_access/stack_selection.README.md |
| GCOV HDF5 diagonal-layer reading | data_access/gcov_reader.py | data_access/README.md |
| Candidate GeoTIFF export | data_access/raster_export.py | data_access/raster_export.README.md |
| Open-water candidate classification | flood/water_classification.py | flood/water_classification.README.md |
| Event inundation accounting | flood/inundation.py | flood/inundation.README.md |
| Persistent erosion/deposition candidates | morphology/persistent_change.py | morphology/persistent_change.README.md |
| Independent-reference metrics and threshold sensitivity | validation/metrics.py, validation/sensitivity.py | validation/README.md |

Each README is adjacent to the code it explains. Read the relevant README before reviewing or evaluating that scientific task.

## Install and test

From Backend:

    python -m pip install -r requirements-river-shift.txt
    python -m pytest tests/river_shift -q

The tests use synthetic fixtures. They verify code contracts, not actual remote-sensing accuracy.

## Current limitations

The science foundation and catalogue-only UI exist. Production processing still needs authenticated GCOV downloads, large-file AOI-windowed reading, documented mask quality interpretation, result manifests, a real-scene run, independent reference labels and a real-scene validation report. Do not display synthetic test results as a real Jamuna event.
