# Scientific module 01 · Raster I/O and spatial comparability

## Role
This module is the safety boundary for raster inputs, grid compatibility, units, area calculations, GeoTIFF writing and GeoJSON polygonization.

## Scientific reason
A pixel-wise difference is meaningful only when pixels refer to comparable ground locations. A raster with a different CRS, affine transform or dimensions must not be silently compared.

## Functions
- read_band: read band 1, create a NoData-aware validity mask, preserve CRS, transform and dimensions.
- assert_same_grid: require exact CRS, shape and affine transform equality.
- require_projected_metre_grid: reject geographic or non-metre CRS before area sums.
- power_to_db: convert positive linear power using 10 log10(power); preserve explicitly declared dB.
- write_mask: export binary classes with 255 as NoData.
- write_mask_geojson: polygonize class pixels and transform geometry to EPSG:4326.
- save_json: write reproducible JSON while rejecting NaN/Infinity.
 
## Validation
Synthetic GeoTIFF tests exercise grid equality, projection requirements, mask values, polygon output and area calculations. Every downstream scientific module imports these functions rather than duplicating its own raster alignment or area math.

## Acceptance / AI review
- No CRS or transform mismatch is silently resampled.
- Area calculation requires projected metre units.
- NoData is excluded from class masks and comparison.
- Gamma0 conversion is power-to-dB with factor 10.
- GeoTIFF output retains CRS and transform.
- GeoJSON output is explicitly reprojected to WGS84.
- JSON output cannot contain NaN or Infinity.

## Limitations
Exact grid equality is deliberately strict. If source grids differ, create a separately documented resampling/reprojection step and justify the target grid before running comparisons.

## References
- Rasterio: https://rasterio.readthedocs.io/
- GDAL: https://gdal.org/
- NISAR GCOV: https://nisar-docs.asf.alaska.edu/gcov/
