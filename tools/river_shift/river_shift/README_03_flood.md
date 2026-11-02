# Scientific module 03 · Three-date flood inundation screening

## Role
Compare before, during and after event water masks and estimate newly water-covered area relative to the pre-event observation.

## Inputs and gates
- Three same-grid GCOV rasters.
- One matching frequency, covariance term and maturity.
- Observation dates tied to a documented event.
- Explicit linear-power or dB units.
- Optional aligned permanent-water reference mask.

## Method
1. Enforce same CRS, dimensions and affine transform.
2. Convert to dB using the declared input contract.
3. Estimate or load one shared threshold.
4. Create before/during/after open-water candidate masks.
5. Calculate new water coverage as during-water AND NOT before-water.
6. Exclude optional permanent-water reference pixels.
7. Sum valid pixel area and export raster/GeoJSON/JSON outputs.

## Metrics
- baseline water area
- peak water area
- post-event water area
- newly water-covered area relative to pre-event
- water-area change percentage

## Validation
The synthetic test checks that an expanded water mask produces a nonzero new-water area, that result provenance is retained, and that mismatched CRS fails closed.

## Acceptance / AI review
- Before/during/after dates are stored.
- Maturity, frequency and covariance term are stored.
- Threshold method and units are stored.
- NoData and permanent-water mask are accounted for.
- Output label says newly water-covered screening.
- The result is marked SCREENING_NOT_INDEPENDENTLY_VALIDATED until a real reference validation exists.

## Limitations
This algorithm does not measure water depth, damage or flood causality. New water relative to a pre-event mask can include seasonal water-level differences. A low-backscatter classifier may miss flooded vegetation. Use the acquisition nearest the hydrological peak rather than a median composite that could hide the peak.

## References
- NISAR GCOV: https://nisar-docs.asf.alaska.edu/gcov/
- FFWC: https://ffwc.gov.bd/
