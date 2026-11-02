# Scientific module 07 · GCOV time-series feasibility and footprint coverage

## Role
Identify compatible NISAR GCOV groups with enough unique observation dates and adequate aggregate footprint coverage of the same AOI.

## Group signature
- Collection maturity (BETA or PROVISIONAL).
- Orbit direction.
- Relative orbit.
- Bandwidth mode.
- Polarization configuration.
- Processing type (PR/UR/OD).

The frame number is recorded but is not used as a grouping split because adjacent frames can contribute to the same AOI mosaic on a single acquisition date. The union of same-date footprint geometry is used for AOI coverage.

## Formula
    AOI coverage (%) = 100 * area(AOI intersect union(date footprints)) / area(AOI)

Area is calculated in a local projected UTM CRS, not directly in square degrees.

## Validation
Synthetic tests verify:
- three dates with matching metadata and complete footprints qualify,
- different relative orbits do not merge into one group,
- incomplete coverage does not pass,
- missing footprint geometry produces an explicit incomplete status.

## Acceptance / AI review
- At least three distinct acquisition dates are required.
- Products with unknown maturity are rejected from qualifying groups.
- Maturity, direction, relative orbit, bandwidth and polarization must match.
- Every qualifying acquisition date must meet the AOI coverage threshold.
- Every chosen granule ID remains in the report.
- Catalogue availability never becomes an accuracy claim.

## Limitations
This is a screening gate for the next raster-processing stage. It cannot prove identical radar viewing geometry, radiometric calibration, hydrological stage or scientific accuracy. Manual footprint review and post-export grid checks remain mandatory.

## References
- ASF API: https://docs.asf.alaska.edu/api/keywords/
- NISAR GCOV: https://nisar-docs.asf.alaska.edu/gcov/
- NISAR naming: https://nisar-docs.asf.alaska.edu/naming-conventions/
