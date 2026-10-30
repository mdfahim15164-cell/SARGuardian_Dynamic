# Scientific module 06 · Signed bankline migration along transects

## Role
Calculate signed bankline movement between two dates along user-oriented fixed cross-sections.

## Scientific reason
A pair of independently interpreted banklines can be compared along perpendicular transects. This is more interpretable than a symmetric nearest-edge distance because the sign is defined by the orientation of each transect.

## Inputs
- Before and after bankline FeatureCollections.
- Transect FeatureCollection.
- Explicit projected metre CRS.
- Two observation dates.
- Explicit meaning of the transect start-to-end direction.
- Provenance for the mission/product/maturity used to interpret the banklines.

## Formula
    before_chainage = distance along transect start -> before-bankline intersection
    after_chainage  = distance along transect start -> after-bankline intersection
    signed_displacement_m = after_chainage - before_chainage
    mean_net_rate_m_per_year = signed_displacement_m / (elapsed_days / 365.25)

## Intersection rule
Each transect must intersect each bankline exactly once. If an intersection is absent or ambiguous (including multiple braided threads), the transect is marked invalid and excluded from summary values.

## Validation
Tests verify:
- exact signed shift on synthetic parallel banklines,
- sign reversal when a transect is digitized in reverse,
- invalid handling for multiple intersections,
- projected-metre CRS requirement,
- date ordering and direction label requirements.

## Acceptance / AI review
- No CRS is inferred silently.
- A geographic CRS is rejected.
- The sign convention is explicit and retained in each output row.
- Invalid transects do not contribute to summary statistics.
- Rate is a two-observation mean net rate, not a long-term migration trend.
- Braided river multiple intersections are surfaced instead of silently choosing one.

## Limitations
The script measures along supplied transects; it does not automatically extract banklines or select which bankline definition is appropriate. Hydrological stage differences and manual digitizing error can dominate small shifts. Review source imagery and linework independently.

## References
- USGS DSAS: https://www.usgs.gov/centers/whcmsc/science/digital-shoreline-analysis-system-dsas
- NISAR GCOV: https://nisar-docs.asf.alaska.edu/gcov/
