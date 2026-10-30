# Comparable-scene and grid-alignment gate

## Scientific task

Before multi-date pixel arithmetic, RiverShift must prove that selected NISAR scenes have comparable acquisition and processing identity and then prove their geospatial grids align.

## Metadata compatibility

The selector requires one:
- ASF-requested / per-product data maturity (PROVISIONAL or BETA).
- Product processing type (PR / UR / OD).
- Relative orbit track.
- Orbit direction.
- Frame number.
- Acquisition mode.
- Polarization mode.
- Source mode.
- CRID.

Cycle number is recorded but not a hard compatibility key because repeat acquisitions in later cycles may revisit a ground track. The largest fully specified group is returned. Unparseable or incomplete scenes are excluded with explicit reasons.

A passing metadata selection is only ready for HDF5 grid checks. Frequency A/B and covariance-term presence must be confirmed inside each downloaded product.

## Raster-grid compatibility

The grid validator requires at least two scenes with:
- Same frequency and diagonal covariance term.
- Same raster shape.
- Equivalent CRS.
- Matching x/y coordinate arrays.

A mismatch raises an exception. No resampling is silently performed. Any future resampling policy requires its own method description and tests.

## Acceptance

- Product-name parser returns known fields from the official NISAR GCOV example.
- Unknown/malformed names return no identity rather than guessed values.
- Mixed track/frame/CRID or maturity groups are not combined.
- Grid mismatch is rejected before pixel-wise change detection.

## Limitation

ASF catalogue properties can omit details. The original granule name remains first-class evidence. A missing product property must not be fabricated from the request form; the query filter and the scene's own reported metadata are stored separately.
