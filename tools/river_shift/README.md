# RiverShift scientific tools

RiverShift is a separate, reproducible NISAR-based river surface-change module in SARGuardian_Dynamic.

## Development scope
This folder provides a first local scientific workflow:
1. Discover NISAR GCOV products in ASF DAAC.
2. Download an exact selected HDF5 granule.
3. Inspect its native diagonal covariance terms.
4. Export one consistently selected AOI-clipped gamma0 layer per acquisition.
5. Screen flood-period new water coverage.
6. Screen persistent erosion/deposition candidates.
7. Validate a binary water mask against an independently prepared reference raster.
8. Measure signed bankline displacement along independently digitised transects.

This is not yet a cloud-dispatched, end-to-end job pipeline. Backend catalogue discovery is available separately. Large HDF5 processing should only be enabled in a worker after an AOI/product feasibility run and resource review.

## Environment
- Python 3.11 or newer.
- GDAL 3.13.0 or newer with HDF5 support.
- Rasterio compatible with the installed GDAL runtime.
- Earthdata Login/ASF access for product downloads.
- A projected metric output CRS; NISAR GCOV is normally provided in UTM for its footprint.

Install Python dependencies from this folder:

    python -m pip install -r requirements.txt

GDAL is a native system dependency. Install and verify it independently:

    gdalinfo --version

The inspection script refuses GDAL versions older than 3.13.0 because the NISAR HDF5 structure uses CF conventions supported by recent GDAL releases.

## Suggested project layout
    data-audit/
      jamuna_gcov.json
    data/
      raw/
      processed/
      reference/
    results/
      flood/
      morphology/
      validation/
      bankline-migration/
      bankline-migration/

Keep raw multi-gigabyte products outside Git. Commit scripts, small test fixtures, README files, output manifests and selected small GeoJSON previews only. Never commit Earthdata credentials or private user data.

## Execution order
Read these task-specific documents before each script:
- README_01_discover_gcov_products.md
- README_02_download_gcov_product.md
- README_03_inspect_gcov_product.md
- README_04_export_gcov_layer.md
- README_05_run_flood_analysis.md
- README_06_run_morphology_analysis.md
- README_07_validate_water_classification.md
- README_08_measure_bankline_migration.md
- README_08_measure_bankline_migration.md

## Bankline transect measurement
For a signed bankline movement measurement, use `measure_bankline_migration.py` only after independently digitising two dated banklines and creating user-oriented transects as WGS84 GeoJSON. The script reprojects them to a declared metric analysis CRS. Each transect must intersect each bankline exactly once; ambiguous braided-channel intersections are rejected. The sign convention is start-to-end along the transect and must be declared in `--positive-direction-label`.

See `README_08_measure_bankline_migration.md` and `river_shift/README_06_transects.md` before running it.

## Data-comparability gate
Before pixel-wise comparison, verify:
- Same NISAR instrument/frequency and acquisition mode.
- Same diagonal covariance term and compatible polarimetric configuration.
- Same maturity (do not mix BETA and PROVISIONAL).
- Compatible orbit direction, relative orbit/track, frame and viewing geometry.
- Same CRS, dimensions and affine transform after reprojection/resampling.
- Dates correspond to a documented hydrological event and recovery condition.

A failed comparability check means stop and reselect/reproject the data. Do not force a pixel-wise overlay.

## Core formulas
For GCOV linear gamma0 power:
    gamma0_dB = 10 * log10(gamma0_power)

For newly water-covered area:
    new_water = water_during AND NOT water_before

For persistent erosion candidate:
    erosion = land_before AND water_post_1 AND water_post_2

For persistent deposition candidate:
    deposition = water_before AND land_post_1 AND land_post_2

The erosion and deposition terms are candidate indicators. They do not establish flood causality or legal/field-confirmed land loss.

For independently digitised banklines and oriented transects:
    signed_displacement_m = after_chainage_m - before_chainage_m
    mean_net_rate_m_per_year = signed_displacement_m / (elapsed_days / 365.25)

Each transect must intersect each bankline exactly once. The transect start-to-end orientation determines the sign; ambiguous intersections are invalid.

## Reproducibility and provenance
Every JSON result should retain:
- Mission and product.
- Exact granule names and checksums (download manifest).
- Observation dates.
- Maturity, frequency and polarization term.
- AOI.
- Input units and threshold method/value.
- Grid/CRS assumptions.
- Software versions.
- Validation status and warnings.

Do not display sample values as measurements. The frontend accepts only generated result JSON and GeoJSON produced by these scripts.

## Test suite
From this folder:

    python -m pip install -r requirements.txt
    python -m pip install pytest
    python -m pytest -q

The tests use small synthetic rasters. They verify contracts and algorithms, not real-world model accuracy. Real scientific validation must use independent observations over the selected study area.

## Scientific references
- NISAR GCOV guide: https://nisar-docs.asf.alaska.edu/gcov/
- NISAR data maturity: https://nisar-docs.asf.alaska.edu/availability-overview/
- NISAR HDF5 guide: https://nisar-docs.asf.alaska.edu/data-format/
- ASF search: https://docs.asf.alaska.edu/api/keywords/
- Jamuna riverbank erosion study: https://nhess.copernicus.org/articles/23/1749/2023/
