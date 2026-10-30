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
- NISAR frame-coverage filter: ALL, FULL or PARTIAL (default ALL for initial discovery).
- Maximum results from 1 to 2000.

`FULL` or `PARTIAL` describes the NISAR frame product. It is not the percentage of the user-defined AOI covered by a scene. See README_09 for per-date footprint coverage.
- Optional NISAR frame-coverage filter (ALL, FULL, PARTIAL; default ALL for discovery).

Important: FULL/PARTIAL is a product-frame metadata field. It does not say how much of the user-drawn AOI is covered; README_09 calculates that percentage from actual footprints.

## Method
1. Validate the WGS84 polygon and date order.
2. Query the ASF Search API with dataset=NISAR, processingLevel=GCOV, intersectsWith, start and end, requesting `output=json`.
3. Parse the official 18-token single-acquisition GCOV granule name, including orbit, frame, bandwidth mode, polarization, timestamps, CRID and FULL/PARTIAL frame coverage; keep ASF-supplied footprint geometry for the separate AOI-coverage audit.
4. Resolve maturity only from the official ASF collection URL/path or explicit collection metadata. A CRID token alone is not used to guess BETA/PROVISIONAL maturity.
5. Write the unmodified catalogue identifiers into a JSON manifest.

## Reproduce
Run from tools/river_shift:

    python -m pip install -r requirements.txt
    python discover_gcov_products.py --aoi-wkt "POLYGON ((89.62 24.43, 89.78 24.43, 89.78 24.68, 89.62 24.68, 89.62 24.43))" --start-date 2026-06-17 --end-date 2026-10-31 --maturity PROVISIONAL --frame-coverage ALL --out data-audit/gcov-catalogue-manifest.json

The coordinates above are the repository's explicitly unapproved Sirajganj–Kazipur candidate AOI. It is for catalogue feasibility only. Obtain science-team approval and replace it before making any study claim.

## Outputs
- JSON manifest containing the query and each matching GCOV granule.
- Product count and non-fabricated warning messages.
- Maturity, acquisition time, relative orbit, direction, frame, mode and polarization when present.

## Acceptance tests
- Invalid geometry and reversed dates fail before network access.
- Product-level filter excludes non-GCOV results.
- The ASF request uses documented `output=json`.
- The official 18-token GCOV filename is parsed; malformed names are rejected.
- Frame coverage ALL/FULL/PARTIAL is preserved separately from AOI footprint percentage.
- Unknown maturity remains UNKNOWN and is not inferred from CRID.
- Official 18-token NISAR L2 GCOV product names are parsed, while malformed/pair-product names are rejected.
- ASF request uses the documented `output=json` format.
- FULL/PARTIAL frame coverage remains distinct from the user-defined AOI coverage percentage.
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
- Confirm maturity comes from the official collection URL/metadata or is marked UNKNOWN.
- Confirm acquisition date, orbit/track, processing type, CRID and frame coverage are retained.
- Confirm all acquisition IDs/dates are retained.
- Confirm the README command is reproducible and placeholders are labelled.
- Confirm no flood/erosion metric is claimed by this script.

## Primary references
- ASF Search API keywords: https://docs.asf.alaska.edu/api/keywords/
- ASF search manual: https://docs.asf.alaska.edu/asf_search/searching/
- NISAR GCOV product guide: https://nisar-docs.asf.alaska.edu/gcov/
- NASA NISAR data: https://science.nasa.gov/mission/nisar/data/
