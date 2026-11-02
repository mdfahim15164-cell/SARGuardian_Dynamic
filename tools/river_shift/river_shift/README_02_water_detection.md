# Scientific module 02 · Open-water candidate classifier

## Role
Convert a declared NISAR GCOV gamma0 raster into a binary low-backscatter open-water candidate mask.

## Scientific reason
Open water often appears as low radar backscatter because a smooth water surface reflects much of the incident microwave energy away from the sensor. This is useful for screening, but it is not a complete water classifier.

## Method
- Convert positive linear gamma0 power to dB where necessary.
- Compare each valid pixel with one threshold expressed in dB.
- Optionally remove connected components smaller than a user-supplied pixel count.
- Otsu threshold estimation is offered as exploratory global threshold selection, not an automatic scientifically validated threshold.

## Equation
    gamma0_dB = 10 * log10(gamma0_power)
    open_water_candidate = valid AND gamma0_dB <= threshold_dB

## Validation
Synthetic tests verify linear-power conversion, threshold behaviour, invalid-pixel exclusion, connected-component filtering and low-sample Otsu failure.

## Acceptance / AI review
- The caller must declare whether input is linear power or dB.
- No conversion is repeated for dB inputs.
- Non-positive linear power is invalid, not water.
- The threshold is a caller-supplied experimental parameter or explicitly labelled exploratory Otsu.
- The output is named open-water candidate, not ground-truth water.
- Flooded vegetation limitations are displayed.

## Limitations
- Flooded vegetation can return bright double-bounce signals and may not be detected by a dark-water threshold.
- Smooth soil, shadow and other dark surfaces can create false positives.
- A single global threshold is not guaranteed to work across different acquisitions, topography or river reaches.
- Optical/reference data and sample-based calibration are needed.

## References
- NISAR GCOV: https://nisar-docs.asf.alaska.edu/gcov/
- NASA SAR applications: https://science.nasa.gov/mission/nisar/
