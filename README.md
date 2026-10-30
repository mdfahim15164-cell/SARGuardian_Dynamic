# SARGuardian Dynamic

SARGuardian is an open-source, multi-engine surface-change monitoring platform. It is being developed for the 2026 NASA Space Apps Challenge, including the challenge **Dancing with the SARs**.

## Current engines
- **Landslide** — existing GUNW/GOFF displacement investigation workflow.
- **RiverShift** — new NISAR GCOV-based flood and river-change monitoring module.
- Glacier Collapse and Farming Activities are planned engines.

## RiverShift

**RiverShift — Flood & River Change Intelligence** is a separate scientific engine designed to track:
1. Flood-period water expansion.
2. Persistent land-to-water transition candidates (river erosion screening).
3. Persistent water-to-land transition candidates (deposition/char screening).
4. Signed bankline movement along reviewed cross-river transects.
5. Independent validation against a reference water mask.

RiverShift uses NASA-ISRO NISAR Level-2 GCOV as its primary radar product. Supporting sources such as Sentinel-2, Bangladesh FFWC and land-cover datasets are used only when they are actually available and are clearly attributed.

### Start here
- [RiverShift architecture](docs/RIVERSHIFT_ARCHITECTURE.md)
- [RiverShift scoring acceptance matrix](docs/RIVERSHIFT_SCORING_ACCEPTANCE.md)
- [RiverShift research decisions and limitations](docs/RIVERSHIFT_RESEARCH_DECISIONS.md)
- [RiverShift implementation checklist](docs/RIVERSHIFT_IMPLEMENTATION_CHECKLIST.md)
- [RiverShift scientific tools and reproducibility](tools/river_shift/README.md)

### Scientific task READMEs
Each script has its own method, inputs, outputs, validation requirements, limitations, reproducibility instructions and AI-review checklist:
- [01 Discover GCOV products](tools/river_shift/README_01_discover_gcov_products.md)
- [02 Download exact GCOV product](tools/river_shift/README_02_download_gcov_product.md)
- [03 Inspect GCOV HDF5](tools/river_shift/README_03_inspect_gcov_product.md)
- [04 Export AOI-clipped GCOV layer](tools/river_shift/README_04_export_gcov_layer.md)
- [05 Flood inundation screening](tools/river_shift/README_05_run_flood_analysis.md)
- [06 River morphology screening](tools/river_shift/README_06_run_morphology_analysis.md)
- [07 Water classification validation](tools/river_shift/README_07_validate_water_classification.md)
- [08 Signed bankline migration](tools/river_shift/README_08_measure_bankline_migration.md)
- [09 GCOV time-series and AOI coverage audit](tools/river_shift/README_09_audit_gcov_acquisitions.md)

### Current implementation status
Implemented in this feature branch:
- Read-only ASF NISAR GCOV catalogue endpoint: POST /api/river-shift/catalog/search.
- Exact-product download utility with host validation and SHA-256 receipt.
- NISAR GCOV HDF5 inventory and AOI-clipped COG export.
- Three-date open-water screening.
- Two-post-observation persistent erosion/deposition candidate screening.
- Confusion matrix, precision, recall, F1, IoU, kappa and area-bias validation.
- Signed transect-based bankline displacement measurement for reviewed bankline and transect inputs.
- NISAR GCOV compatibility and AOI footprint coverage audit with a manual GitHub Actions workflow.
- A candidate Sirajganj–Kazipur AOI, explicitly not approved as the final study polygon.
- Separate public frontend route at /river-shift.
- Catalogue, scientific-result and GeoJSON inspection UI.
- Per-task and per-module scientific READMEs, signed bankline transect measurement, and regression tests.

### Not yet claimed
A real Jamuna study event, available NISAR granule count, flood area, erosion area, accuracy score or measured migration rate has **not** been established by this code change. The first research milestone is running the manual ASF GCOV audit workflow with a team-approved AOI. A candidate Sirajganj–Kazipur polygon is included only for initial feasibility testing. The morphology boundary distance is a symmetric screening proxy. The separate signed transect tool requires independently digitised banklines and oriented transects; it is not an automatic NISAR bankline extractor. GCOV processing is currently run through local CLI tools; a durable cloud-dispatched RiverShift worker and Supabase job schema are future integration work.

## Run the frontend
From Frontend:

    npm ci
    npm run dev

Set the documented public frontend configuration in Frontend/.env.local. The RiverShift catalogue endpoint uses VITE_SARGUARDIAN_API_URL. The satellite map requires VITE_GOOGLE_MAPS_API_KEY.

## Run the backend
From Backend, configure server-side environment variables from .env.example and follow Backend/README.md. Never place Supabase server credentials, Earthdata tokens or Firebase Admin credentials in a VITE_ variable.

## Test
Frontend:

    cd Frontend
    npm ci
    npm run build
    npm run lint
    npm test

Backend:

    cd Backend
    python -m pip install -r requirements-test.txt
    python -m pytest -q

RiverShift science:

    cd tools/river_shift
    python -m pip install -r requirements.txt
    python -m pip install pytest
    python -m pytest -q

The science tests use synthetic rasters and validate implementation contracts only. They are not claims of real-world accuracy.

## Challenge
2026 NASA Space Apps Challenge — Dancing with the SARs.

Official challenge: https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/
NASA NISAR data: https://science.nasa.gov/mission/nisar/data/
ASF NISAR GCOV guide: https://nisar-docs.asf.alaska.edu/gcov/

## Open science
Record real granule identifiers, product maturity, acquisition dates, product version, input units, code versions, independent reference sources, validation metrics and known limitations with every published result.
