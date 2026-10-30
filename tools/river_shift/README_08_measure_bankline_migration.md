# 08 · Signed bankline migration along transects

## Purpose
Measure signed bankline displacement between two observation dates along user-supplied cross-river transects. This provides a directional bank-migration measurement, unlike the symmetric boundary-distance proxy in the morphology screening task.

## NASA challenge relevance
NISAR time-series observations can reveal changes in river boundaries. This task translates independently interpreted banklines from two observation dates into reproducible metres of movement along fixed cross-sections. The banklines may be digitised from NISAR-derived products and checked against supporting optical imagery.

## Inputs
- Before-event bankline as GeoJSON LineString/MultiLineString.
- After-event bankline as GeoJSON LineString/MultiLineString.
- Transect lines as GeoJSON LineString features.
- A projected metre CRS for all three vector inputs, e.g. the appropriate UTM zone.
- Before and after observation dates.
- A user-declared positive-direction label that matches the orientation from each transect's first coordinate to its last coordinate.
- Source mission/product and maturity metadata.

GeoJSON inputs follow RFC 7946 and use WGS84 coordinates. The script reprojects them into the explicitly declared metric analysis CRS before intersection and distance calculations.

## Method
1. Load and validate the bankline and transect FeatureCollections.
2. Validate that the declared CRS is projected and its linear units are metres.
3. Require the after date to be later than the before date.
4. For every transect, intersect it with each bankline.
5. Accept a measurement only when each transect intersects each bankline exactly once.
6. Measure the distance (chainage) along the transect from its first coordinate to each intersection.
7. Calculate signed displacement:
       displacement_m = after_chainage_m - before_chainage_m
8. Calculate the mean net rate between the two selected dates:
       mean_net_rate_m_per_year = displacement_m / (elapsed_days / 365.25)
9. Mark ambiguous or missing intersections invalid and exclude them from summary statistics.
10. Export per-transect CSV, GeoJSON and a provenance-rich JSON summary.

## Reproduce
Prepare three vector GeoJSON files in EPSG:4326 (WGS84). The analysis CRS is selected separately as a projected metre CRS. Each transect must be digitised from the documented stable/landward side toward the documented channel side if positive means channelward.

    python measure_bankline_migration.py --before-bankline data/vector/bankline_before.geojson --after-bankline data/vector/bankline_after.geojson --transects data/vector/transects.geojson --analysis-crs EPSG:32646 --before-date 2026-06-01 --after-date 2026-09-01 --positive-direction-label toward_channel --source-mission NISAR --source-product GCOV --maturity PROVISIONAL --out-dir results/bankline-migration

The dates, CRS, positive direction and file paths are illustrative. Use the actual CRS and dates associated with the chosen study area.

## Outputs
- bankline_migration.csv: each transect, intersection status, chainages, signed displacement and mean net rate.
- bankline_migration_transects.geojson: transect features and computed properties in EPSG:4326 for mapping.
- bankline_migration_summary.json: study dates, source metadata, formulas, aggregate statistics, invalid counts and warnings.

## Metrics
- Number of transects.
- Valid/invalid transect counts.
- Mean and median signed displacement (m).
- P95 absolute displacement (m).
- Mean net rate between the selected dates (m/year).
- Positive, negative and unchanged transect counts.

## Acceptance tests
- Geographic CRS or non-metre CRS is rejected.
- Reversed/identical dates are rejected.
- Missing positive-direction label is rejected.
- Every transect must be a LineString with positive length.
- A transect with anything other than exactly one intersection with each bankline is marked invalid, not guessed.
- The signed distance equals after chainage minus before chainage.
- Reversing transect coordinate order reverses the displacement sign.
- Invalid transects are excluded from aggregates.
- Summary retains the explicit positive-direction label and elapsed dates.
- Rates are described as mean net displacement between two dates, not long-term trend.

## Scientific limitations
- Banklines must be consistently digitised using a documented definition (e.g. active channel edge, waterline, or outer active-channel belt).
- Water stage can shift the apparent waterline even when the geomorphic bank has not moved. Prefer comparable hydrological stages and independent imagery.
- A braided river may intersect one transect many times. Such transects are flagged as ambiguous by this implementation; use a separately defined outer active-channel belt bankline if that is the research target.
- A positive sign means only the user-declared transect direction. It is not inherently erosion or accretion until the digitizing orientation and which bank is being measured are interpreted correctly.
- Two-date net rates are not forecasts and do not establish causality.

## AI reviewer checklist
- Verify the same projected metre CRS is used for banklines and transects.
- Verify each transect is oriented consistently and the positive direction label is explicit.
- Verify exact-one-intersection rules are enforced.
- Verify displacement is after chainage minus before chainage.
- Verify rate is elapsed-date-normalized and not presented as a long-term trend.
- Verify ambiguous braided-channel transects are marked invalid.
- Verify source/date/CRS/method provenance appears in the output.

## Primary references
- NISAR GCOV guide: https://nisar-docs.asf.alaska.edu/gcov/
- USGS Digital Shoreline Analysis System (transect-based change methodology): https://www.usgs.gov/centers/whcmsc/science/digital-shoreline-analysis-system-dsas
- Bangladesh Jamuna riverbank erosion study: https://nhess.copernicus.org/articles/23/1749/2023/
