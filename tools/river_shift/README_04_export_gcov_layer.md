# 04 · Export one AOI-clipped GCOV layer

## Purpose
Extract one calibrated diagonal covariance layer from a NISAR GCOV HDF5 product and export the exact selected AOI as a Cloud Optimized GeoTIFF (COG).

## NASA challenge relevance
This step turns native NISAR HDF5 data into a geospatial raster that can be analysed, validated, mapped and shared in an interactive surface-change application.

## Inputs
- Exact GCOV HDF5 file.
- Frequency: frequencyA or frequencyB.
- One available diagonal covariance term.
- Valid WGS84 Polygon WKT.
- Explicit product maturity.

## Method
1. Inspect the HDF5 subdataset inventory.
2. Verify that the requested frequency and diagonal term exist.
3. Convert the AOI WKT into a temporary GeoJSON cutline.
4. Use GDAL warp to clip the subdataset to the AOI.
5. Convert the clipped raster to COG format.
6. Write a metadata sidecar stating source product, maturity, frequency, term and units.

## Reproduce
    python export_gcov_layer.py --product data/raw/EXACT_GRANULE.h5 --frequency frequencyA --term VVVV --maturity PROVISIONAL --aoi-wkt "POLYGON ((89.60 25.10, 89.90 25.10, 89.90 25.35, 89.60 25.35, 89.60 25.10))" --out data/processed/date_frequencyA_VVVV.tif

The polygon and granule above are syntax examples, not verified study inputs.

## Outputs
- AOI-clipped COG.
- Metadata sidecar with the exact source HDF5 file and gamma0_power units.

## Acceptance tests
- Invalid geometry or unsupported maturity fails.
- An absent polarization term fails before GDAL export.
- The output is clipped to the requested AOI.
- The metadata sidecar records the frequency, term, maturity and gamma0 power units.
- Intermediate files are cleaned up on success.

## Scientific limitations
- Do not mix different maturity versions, frequencies, polarizations, modes, orbit directions or incompatible grids in one pixel-wise comparison.
- A matching term name alone does not prove identical incidence geometry or acquisition conditions.
- Preserve the NISAR source granule and checksum alongside the COG.

## AI reviewer checklist
- Verify the term is one of the real-valued diagonal layers.
- Verify the extraction source is the NISAR GCOV HDF5 subdataset.
- Verify the AOI is explicitly clipped.
- Verify product maturity and unit provenance is preserved.
- Verify GDAL 3.13 support is documented.

## Primary references
- NISAR GCOV guide: https://nisar-docs.asf.alaska.edu/gcov/
- NISAR HDF5 guide: https://nisar-docs.asf.alaska.edu/data-format/
- GDAL NISAR guide: https://nisar-docs.asf.alaska.edu/using-nisar-data/using-gdal/
