# RiverShift

**Flood & River Change Intelligence** — a NISAR-first surface-change monitoring engine inside SARGuardian.

RiverShift is being developed for the 2026 NASA Space Apps Challenge **“Dancing with the SARs”**. Its purpose is to make repeat-pass radar observations understandable as evidence of flood inundation and persistent river-system change.

## What it measures

1. **Flood inundation:** newly water-covered pixels during an event, relative to a pre-event baseline.
2. **River change candidates:** land-to-persistent-water transitions (erosion candidates) and water-to-persistent-land transitions (deposition candidates).
3. **Riverbank movement:** a later geometry stage will extract comparable banklines and measure displacement using fixed transects.
4. **Exposure context:** a later overlay will intersect observed change with independently sourced settlement and agricultural layers.

RiverShift keeps temporary floodwater separate from persistent channel morphology. A wider river during peak flow is not, by itself, proof of permanent channel migration.

## Architecture

```text
Frontend (RiverShift workspace)
   |
FastAPI (authenticated request + job contract)
   |
ASF NISAR catalogue (GCOV / PROVISIONAL)
   |
GitHub Actions worker (large-file download + science execution)
   |
GCOV HDF5 reader -> calibrated backscatter -> water classification
                                  |                |
                                  |                +-> event inundation metrics
                                  |
                                  +-> multi-date persistence -> erosion/deposition candidates
   |
Validation (reference labels, confusion matrix, sensitivity report)
   |
GeoTIFF/COG + GeoJSON + JSON provenance -> private result storage
   |
Supabase job metadata -> frontend result viewer
```

The scientific package is deliberately independent of the existing Landslide/GUNW/GOFF processor. Existing authentication, durable job patterns, callbacks, GitHub Actions orchestration and private result storage can be reused after an explicit integration review. RiverShift must not change the scientific meaning of the Landslide engine.

## NISAR data strategy

- **Primary input:** NISAR Level-2 GCOV (Geocoded Polarimetric Covariance), beginning with L-band and diagonal covariance power terms.
- **Optional companion:** GSLC when a task specifically needs complex single-look data or a separately validated amplitude workflow.
- **Maturity policy:** one processing maturity / CRID per comparison stack. Do not silently mix BETA and PROVISIONAL.
- **HDF5:** read the documented GCOV group and coordinate/projection metadata; do not assume a fixed EPSG or pixel size.
- **Supporting evidence:** Sentinel-2, FFWC water-level observations, DEM and land-cover layers. These are supporting/validation sources, not substitutes for the challenge's NISAR core.

## Scientific boundaries

- Open-water thresholding is a **candidate classifier**, not a universal water detector. Thresholds must be calibrated for the scene, polarization, local land cover and reference samples.
- Flooded vegetation can have strong double-bounce returns. A low-backscatter-only method can omit it; the first implementation reports this limitation.
- Erosion/deposition outputs are **change candidates** until persistence, comparable hydrological conditions and reference validation pass.
- This pipeline does not estimate flood depth, predict a flood, establish causation, or issue a public safety warning.
- No numerical result is valid unless it carries source product IDs, acquisition times, processing maturity, algorithm parameters, grid metadata and validation status.

## Development status

This repository currently contains the independent science foundation: GCOV metadata discovery, HDF5 inspection, open-water candidate classification, inundation accounting, persistent-change candidates and validation metrics. Product download orchestration, production raster/COG export, bankline transects, API jobs and the full interactive workspace remain subsequent milestones.

## Run the science tests

From the repository root:

```bash
python -m pip install -r river_shift/requirements-river-shift.txt
python -m pytest river_shift/tests -q
```

All tests use small synthetic arrays or synthetic HDF5 fixtures. They test calculations and contracts; they are **not** a claim of accuracy on real Jamuna observations.

## Documentation map

- [Architecture and data flow](../docs/RIVERSHIFT_ARCHITECTURE.md)
- [Scorecard acceptance plan](../docs/RIVERSHIFT_SCORECARD_ACCEPTANCE.md)
- [Science data contract](../docs/RIVERSHIFT_DATA_CONTRACT.md)
- [GCOV data access README](science/data_access/README.md)
- [Water classification README](science/flood/water_classification/README.md)
- [Inundation accounting README](science/flood/inundation/README.md)
- [Persistent river-change README](science/morphology/persistent_change/README.md)
- [Validation README](science/validation/README.md)
- [Test plan](tests/README.md)
