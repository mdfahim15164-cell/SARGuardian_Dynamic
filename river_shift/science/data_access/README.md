# Data access and GCOV reading

## Purpose

This folder implements the NISAR-first data boundary for RiverShift. It discovers GCOV scenes from ASF and reads a requested calibrated diagonal covariance layer from a NISAR GCOV HDF5 product.

## Why GCOV?

NISAR's Level-2 GCOV product is radiometrically terrain-corrected backscatter and is explicitly intended to support inundation mapping, disturbance detection and crop-area delineation. RiverShift uses GCOV as its primary radar input rather than reusing the existing GUNW/GOFF displacement downloader.

## Catalogue discovery

`catalog.py` calls the supported `asf_search` API with:
- `dataset="NISAR"`
- `processingLevel="GCOV"`
- `dataMaturity="PROVISIONAL"` by default
- AOI polygon, date window and a bounded result count.

The function returns catalogue metadata only. It does not download data and does not claim that a scene is scientifically comparable until the stack-selection checks are completed.

## HDF5 reader contract

`gcov_reader.py` reads a diagonal covariance dataset under:

```
/science/LSAR/GCOV/grids/frequencyA|frequencyB/
  HHHH | HVHV | VVVV | VHVH | RHRH | RVRV
```

It reads the `xCoordinates`, `yCoordinates` and `projection` datasets from the same frequency grid. Coordinate arrays are used to check raster dimensions and regularity. The CRS is resolved from the projection value/attributes; it is never hard-coded to a Bangladesh UTM zone.

Only real-valued diagonal terms represent power/intensity. Complex off-diagonal covariance terms are not accepted by this reader.

The reader treats finite positive power as numerically valid and, when available, requires `numberOfLooks > 0`. It does not interpret undocumented mask bits.

## Units

GCOV diagonal terms are gamma-naught power in linear units. Convert to decibels only with:

```
gamma0_db = 10 * log10(gamma0_power)
```

Gamma-naught and sigma-naught are not interchangeable. The product's `rtcGammaToSigmaFactor` can be applied in a separately specified conversion step when sigma-naught is explicitly required.

## Validation before use

- Product must contain the requested GCOV frequency and diagonal term.
- Raster shape must agree with x/y coordinate lengths.
- Coordinates must be monotonic and regularly spaced.
- Projection must resolve to a valid projected CRS.
- Pixel area is calculated from coordinate spacing and CRS axis units.
- Invalid/zero/negative power is excluded, not replaced with arbitrary values.

## Known limitations

The reader currently loads the selected array into memory. Production processing must crop to the AOI/window or stream chunks for large granules. A real-product validation run is required before any published RiverShift metrics are treated as observations.
