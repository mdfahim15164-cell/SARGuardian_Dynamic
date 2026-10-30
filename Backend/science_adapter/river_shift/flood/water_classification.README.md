# Open-water candidate classification

## Scientific task

Convert a NISAR GCOV diagonal covariance power layer into a binary **open-water candidate** mask. This is the first reproducible classification baseline, not a final all-condition flood classifier.

## Input

- 2-D real-valued diagonal GCOV power array (linear gamma-naught power).
- Optional Boolean validity mask.
- One of:
  - `method="otsu"`: data-adaptive threshold estimated from the valid pixels in dB.
  - `method="fixed"`: an explicitly supplied dB threshold. This is useful for controlled calibration and sensitivity experiments.

## Method

1. Convert positive linear power to decibels: `10 * log10(power)`.
2. Exclude non-finite, zero/negative and caller-invalid pixels.
3. For Otsu, estimate the threshold using a histogram over the 2nd–98th percentile range to limit extreme outliers.
4. Pixels at or below the threshold are marked as low-backscatter open-water candidates.

## Required interpretation

Radar backscatter depends on surface roughness, dielectric properties, vegetation structure, polarization and acquisition geometry. Smooth open water often gives low return, but flooded vegetation may generate double-bounce/high returns. This classifier can therefore miss some inundation and can confuse other smooth surfaces with water.

Do not publish the result as a validated flood map until it has been compared with independent reference labels (e.g. cloud-free Sentinel-2 water indices/visual interpretation and local event information) and sensitivity has been assessed.

## Parameters to report

- Source granule ID and checksum.
- Frequency and covariance term.
- Data maturity / CRID.
- Method and threshold in dB.
- Number and percentage of valid pixels.
- Any ancillary quality mask applied.

## Validation

Unit tests cover known two-class synthetic distributions, no-data handling, invalid input rejection and threshold reproducibility. These are software tests, not real-scene accuracy validation.
