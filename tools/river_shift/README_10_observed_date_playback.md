# 10 · Observed-date water time series

## Purpose

Export a water-candidate mask and GeoJSON for each comparable GCOV acquisition so the dashboard can step through the actual observed dates. The player advances between acquisitions. It does not create daily values or interpolate a flood movie.

## Inputs and comparability

- At least two AOI-clipped GCOV-derived rasters, one per distinct acquisition date.
- The same projected metre grid, maturity, frequency and diagonal covariance term.
- Exact observation dates and the declared raster units.
- Matching exporter metadata sidecars for complete granule and checksum provenance. Inputs without sidecars may be useful for software exploration but remain provenance-incomplete.
- One fixed threshold selected through independent validation, or exploratory Otsu over all selected dates.

The command fails closed on different CRS, dimensions, affine transforms, duplicate dates, or mismatched GCOV sidecars. Per-date valid-pixel fraction is reported because changing NoData coverage can make area comparisons misleading.

## Reproduce

From `tools/river_shift`:

```sh
python run_water_timeseries.py \
  --observation 2026-06-18=data/processed/2026-06-18.tif \
  --observation 2026-06-30=data/processed/2026-06-30.tif \
  --observation 2026-07-12=data/processed/2026-07-12.tif \
  --threshold-db -12 --input-units linear \
  --maturity PROVISIONAL --frequency frequencyA --term HHHH \
  --out-dir results/water-timeseries
```

Dates and threshold above are examples, not approved Sirajganj event selections or universal calibration values. Replace them with the dates, granules and threshold supported by your study evidence.

## Outputs

- `water_YYYY-MM-DD_mask.tif` and `water_YYYY-MM-DD.geojson` for every acquisition.
- `river_shift_timeseries.json` with ordered dates, individual area and valid-pixel coverage, granule/source/input/output SHA-256 values, and five deterministic threshold sensitivity scenarios.
- Reports are always `PROVISIONAL` until independent review evidence is recorded. The dashboard animation only appears for a report accepted by its existing verification gate and GeoJSON checksum check.

## Interpretation

Each frame is an observation on the NISAR acquisition date. NISAR does not observe this corridor every day, so the player labels exact dates and never invents daily images. Water-area differences can reflect water stage, radar geometry, threshold, and valid-mask coverage. Low-backscatter screening may omit flooded vegetation and include smooth soil or radar shadow. This is not a causal flood attribution, a validated flood extent, or a bank-migration rate. Use the separate flood-expansion, persistent morphology, independent validation and transect bankline tools for those distinct questions.

## Uncertainty

The report recomputes per-date area at five nearby thresholds. This is deterministic threshold sensitivity only; it is not a statistical confidence interval and excludes reference error, calibration, geolocation, stage and model uncertainty. Independent dated reference data are required to report accuracy.
