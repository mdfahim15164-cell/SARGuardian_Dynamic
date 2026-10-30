# Data access and GCOV reading

## Purpose

This folder provides RiverShift's NISAR-first data boundary: live ASF GCOV catalogue discovery, granule identity parsing, multi-date stack selection, HDF5 reading and candidate raster export.

## Why GCOV?

NISAR Level-2 GCOV provides radiometrically and terrain-corrected backscatter in gamma-naught power. It is suitable for SAR amplitude/inundation mapping and disturbance analysis. RiverShift uses GCOV as its primary radar input instead of reusing the existing Landslide GUNW/GOFF displacement pipeline.

## Data maturity

The catalogue query accepts one explicit ASF maturity filter: PROVISIONAL or BETA. Per-granule reported maturity is stored separately from the query filter. If the archive does not report a per-product field, RiverShift leaves that field null and records that the request filter is the evidence. Never pretend the request filter is a granule property.

Do not mix PROVISIONAL and BETA products in one comparison stack.

## HDF5 reader contract

gcov_reader.py reads a real-valued diagonal covariance dataset beneath:

    /science/LSAR/GCOV/grids/frequencyA|frequencyB/
      HHHH | HVHV | VVVV | VHVH | RHRH | RVRV
      xCoordinates
      yCoordinates
      projection

Not all products contain all possible terms. Available frequencies and polarizations depend on the acquisition mode. The off-diagonal covariance terms are complex and are not accepted as simple intensity images.

The reader checks dimensions, regular coordinate spacing, finite positive power, and numberOfLooks > 0 where that layer exists. It resolves CRS from the projection dataset or its CRS/CF attributes; it does not infer a Bangladesh UTM zone.

## Scene identity and stack compatibility

Read these task guides before comparing dates:

- Granule identity parser: scene_identity.README.md
- Comparable-scene and grid-alignment gate: stack_selection.README.md

The parser extracts instrument band, processing type, cycle, relative orbit, direction, frame, mode, polarization mode, source, time and CRID from the documented NISAR name. Unrecognized names are not guessed.

The stack selector requires one maturity and common acquisition/processing identity. It records the cycle number but does not use it as a hard identity key. It then requires the downloaded HDF5 products to share frequency, covariance term, shape, CRS and x/y coordinate arrays before pixel-wise arithmetic.

## Units and pixel area

GCOV diagonal covariance terms are gamma-naught power in linear units. Convert to decibels with:

    gamma0_db = 10 * log10(gamma0_power)

Gamma-naught and sigma-naught are not interchangeable. If sigma-naught is required, use the product's rtcGammaToSigmaFactor according to its product definition.

Pixel area is derived from source coordinate spacing and projected CRS axis units. It is not hard-coded to 10 m or 100 m². Frequency A products may have 10 m or 20 m spacing, and Frequency B products may have different spacing.

## Candidate raster export

Read raster_export.README.md. The current exporter creates a single-band mask:
- 0 = valid non-water candidate.
- 1 = open-water candidate.
- 255 = NoData.

The dataset is tagged as a candidate result and not an independently validated flood map.

## Limitations

- The current HDF5 reader loads the selected layer into memory. Large products need AOI-windowed or chunked reading.
- The GCOV mask dataset exists, but its documented semantics have not yet been decoded into a RiverShift quality policy. Do not silently ignore this in a production validation run.
- A real NISAR product test is still required. Synthetic fixtures verify software contracts, not real-scene accuracy.
