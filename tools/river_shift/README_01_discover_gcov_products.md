# 01 · Discover NISAR GCOV products

## Purpose
Find real NISAR Level-2 GCOV granules intersecting a single WGS84 study polygon and an acquisition-date interval. This is catalogue discovery only. It does not download imagery, run science processing, or claim a flood result.

## NASA challenge relevance
This is the data-acquisition gate for the NASA Space Apps 2026 challenge “Dancing with the SARs”. The output records NASA-ISRO NISAR product identifiers and ASF DAAC provenance so the later analysis can show that NISAR is the primary data source.

## Scientific question
Does the selected AOI have enough compatible NISAR GCOV acquisitions to support a multi-date backscatter change analysis?

## Inputs
- One valid, non-empty Polygon WKT in EPSG:4326, coordinates ordered longitude then latitude.
- Inclusive acquisition start and end dates.
- Maturity filter: PROVISIONAL, BETA, or ALL (ALL is for auditing; do not mix maturities in one time series).
- Optional Frequency-A main-band polarization and orbit direction.
- Maximum results from 1 to 2000.

## Method
1. Validate the WGS84 polygon and date order.
2. Query the ASF Search API with dataset=NISAR, processingLevel=GCOV, intersectsWith, start and end.
3. Read the actual granule name, acquisition timestamps, orbit direction, product URL, reported size, polarization metadata and track/frame fields when supplied.
4. Infer maturity from the official ASF NISAR collection path. Unknown maturity is never silently relabelled.
5. Write the unmodified catalogue identifiers into a JSON manifest.

## Reproduce
Run from tools/river_shift:

    python -m pip install -r requirements.txt
    python discover_gcov_products.py --aoi-wkt "POLYGON ((89.60 25.10, 89.90 25.10, 89.90 25.35, 89.60 25.35, 89.60 25.10))" --start-date 2026-06-17 --end-date 2026-10-31 --maturity PROVISIONAL --out data-audit/jamuna_gcov.json

The coordinates above are a syntax example only, not a verified Jamuna AOI. Select and document the actual polygon before research runs.

## Outputs
- JSON manifest containing the query and each matching GCOV granule.
- Product count and non-fabricated warning messages.
- Maturity, acquisition time, relative orbit, direction, frame, mode and polarization when present.

## Acceptance tests
- Invalid geometry and reversed dates fail before network access.
- Product-level filter excludes non-GCOV results.
- BETA and PROVISIONAL products remain separated.
- The reported count equals the number of manifest products.
- No-data and result-cap warnings are preserved.
- Every returned granule name and URL originates from ASF response data.

## Scientific limitations
- Catalogue intersection means the product footprint intersects the AOI; it does not guarantee full AOI coverage.
- The presence of multiple products does not prove that they share the same observation geometry, pixel grid, polarization or maturity.
- A catalogue hit is not an analysis result.
- ASF may report missing metadata; missing fields remain unknown rather than being inferred.

## AI reviewer checklist
- Confirm the endpoint is ASF DAAC and the dataset is NISAR.
- Confirm processingLevel is GCOV.
- Confirm maturity is explicit or marked UNKNOWN.
- Confirm all acquisition IDs/dates are retained.
- Confirm the README command is reproducible and placeholders are labelled.
- Confirm no flood/erosion metric is claimed by this script.

## Primary references
- ASF Search API keywords: https://docs.asf.alaska.edu/api/keywords/
- ASF search manual: https://docs.asf.alaska.edu/asf_search/searching/
- NISAR GCOV product guide: https://nisar-docs.asf.alaska.edu/gcov/
- NASA NISAR data: https://science.nasa.gov/mission/nisar/data/
