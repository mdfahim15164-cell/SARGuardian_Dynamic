# RiverShift — Scientific Data Contract

## 1. Product-level contract

| Field | Requirement |
|---|---|
| Mission | NISAR |
| Primary product | GCOV (Level 2, geocoded polarimetric covariance) |
| Frequency | L-band for the first pilot; record actual frequency A/B |
| Covariance layer | Real diagonal term only (e.g. VVVV, HHHH, HVHV) |
| Data maturity | Explicit PROVISIONAL or BETA; do not mix in one stack |
| Time | UTC acquisition start/stop timestamps |
| Geometry | AOI WGS84 polygon; products may use projected grids |
| Quality | finite positive power and numberOfLooks > 0 when layer exists |
| Provenance | granule, URL/ID, maturity, CRID, time, path/frame, frequency, term, processing parameters |

Official references:
- NISAR product overview: https://nisar-docs.asf.alaska.edu/products-overview/
- GCOV product details: https://nisar-docs.asf.alaska.edu/gcov/
- HDF5 data structure: https://nisar-docs.asf.alaska.edu/data-format/
- ASF Search NISAR examples: https://nisar-docs.asf.alaska.edu/asf-search/

## 2. GCOV HDF5 paths

Expected groups:
```
/science/LSAR/GCOV/grids/frequencyA|frequencyB/
    HHHH
    HVHV
    VVVV
    VHVH
    RHRH
    RVRV
    xCoordinates
    yCoordinates
    projection
    numberOfLooks (when present)
    mask (when present)
    rtcGammaToSigmaFactor (when present)
```

Only real diagonal covariance terms are accepted as backscatter power. The off-diagonal covariance terms are complex-valued and must not be treated as a simple intensity layer.

## 3. Units and conversions

GCOV diagonal covariance terms represent gamma-naught power (linear scale). Decibels are:

```
power_db = 10 * log10(power_linear)
```

If sigma-naught is required, use the product-provided RTC gamma-to-sigma factor as defined by the product specification. Do not relabel gamma-naught as sigma-naught.

## 4. Grid / area contract

The source coordinate arrays define pixel centre positions. The pixel area is derived from x/y coordinate spacing and projected CRS axis unit conversion factors. It is not hard-coded to 100 m² or 10 m x 10 m.

Before pixel-wise change detection, scenes must share:
- same CRS,
- same x/y spacing,
- same width/height,
- same grid origin/transform,
- documented resampling policy if exact grids differ.

Resampling a categorical water mask must use nearest-neighbour. Continuous backscatter resampling requires a separately documented method.

## 5. Catalogue query contract

ASF Search supports NISAR discovery with:
```python
asf_search.search(
    dataset="NISAR",
    processingLevel="GCOV",
    dataMaturity="PROVISIONAL",
    intersectsWith=<WGS84 polygon WKT>,
    start=<UTC timestamp>,
    end=<UTC timestamp>,
    maxResults=<bounded integer>,
)
```

Catalogue discovery is metadata-only. Search results are not data downloads and do not constitute science eligibility.

## 6. Current output contracts

### Open-water classification
- `water_mask`: Boolean [y, x].
- `valid_mask`: Boolean [y, x].
- `threshold_db`: threshold applied to gamma0 dB.
- `method`: Otsu or fixed.
- counts of valid and candidate pixels.

### Event inundation
- `newly_inundated_mask`: event water and not baseline water, restricted to common valid pixels.
- baseline/event/new inundated area in km².
- percent water-area change; null when baseline area is zero.

### Persistent morphology candidates
- multiple post-event water masks [time, y, x].
- minimum valid post-event observation count.
- per-pixel post-event water fraction.
- erosion and deposition candidate masks/areas.
- no causal attribution.

## 7. No-data and uncertainty

- Invalid data must remain invalid.
- A pixel without sufficient post-event observations cannot confirm persistence.
- A candidate is not a validated erosion/deposition claim.
- A result missing source provenance is not eligible for publication.
- All dates in reports must be UTC with timezone context.
