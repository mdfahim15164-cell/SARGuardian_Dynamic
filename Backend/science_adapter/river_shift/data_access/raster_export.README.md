# GeoTIFF export

This exporter writes an open-water candidate mask on the source GCOV grid.

## Encoding

- 0 = valid non-water candidate.
- 1 = valid open-water candidate.
- 255 = no-data / invalid input.

The GeoTIFF uses the source EPSG and derives an affine transform from the x/y pixel-centre coordinates. Axis direction is normalized to north-up by flipping the array when required. Irregular axes are rejected rather than silently assigned a false transform.

## Required metadata

The band and dataset tags retain NISAR source path, frequency, covariance term, units, classifier method and threshold. The output is explicitly labelled as a candidate classification.

## Limitations

This is a single-scene classification export. It is not a flood-event polygon or a validated inundation product. AOI cropping, COG creation, overview pyramids and multi-scene stack alignment are later steps.
