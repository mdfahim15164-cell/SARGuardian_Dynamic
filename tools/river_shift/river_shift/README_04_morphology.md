# Scientific module 04 · Persistent land/water morphology candidates

## Role
Compare one pre-event and two post-recession observations to identify candidate persistent land-to-water and water-to-land transitions.

## Definitions
    erosion_candidate = LAND_before AND WATER_post_one AND WATER_post_two
    deposition_candidate = WATER_before AND LAND_post_one AND LAND_post_two

These definitions are screening proxies. They are not causal proof and do not establish legal or field-confirmed erosion/accretion.

## Boundary distance
The module calculates a symmetric nearest-boundary distance between binary water-mask edges. The mean and P95 are descriptive distances between boundary sets. They do not indicate signed bank retreat/accretion direction and must not be described as an annual migration rate.

## Validation
Synthetic rasters verify positive erosion/deposition candidate areas and positive symmetric boundary distances.

## Acceptance / AI review
- Two distinct post-event observations are recorded.
- All rasters pass the same-grid and projected-metre checks.
- Candidate equations match the definitions above.
- Erosion/deposition areas are reported in hectares.
- Boundary output is labelled symmetric distance proxy.
- Result quality says persistence screened but not independently validated.
- Interpretation includes seasonality, braided channel and human-intervention limitations.

## Limitations
A land/water transition can be caused by stage differences, vegetation, shadow, dredging, embankments, sand mining or bank protection. Two post dates reduce transient-water confusion but do not replace independent bankline interpretation. Braided rivers need separate analysis of channel threads and outer active-channel belt.

## References
- NISAR GCOV: https://nisar-docs.asf.alaska.edu/gcov/
- DSAS: https://www.usgs.gov/centers/whcmsc/science/digital-shoreline-analysis-system-dsas
- Bangladesh Jamuna study: https://nhess.copernicus.org/articles/23/1749/2023/
