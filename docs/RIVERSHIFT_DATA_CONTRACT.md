# RiverShift — Scientific Data Contract

## 1. Product-level contract

| Field | Requirement |
|---|---|
| Mission | NISAR |
| Primary product | GCOV (Level 2, geocoded polarimetric covariance) |
| Instrument | L-band for initial pilot; record L/S for every granule |
| Frequency | Record frequency A/B per product |
| Covariance layer | Real diagonal term only (e.g. VVVV, HHHH, HVHV) |
| Data maturity | One explicit PROVISIONAL or BETA stack; do not mix |
| Time | UTC acquisition start/stop timestamps |
| Geometry | AOI WGS84 polygon; GCOV raster may use projected CRS |
| Quality | finite positive covariance power and numberOfLooks > 0 where supplied |
| Provenance | granule, product ID, maturity evidence, CRID, band, mode, track/frame, time, frequency, term and processing parameters |

Official references:
- NISAR product overview: https://nisar-docs.asf.alaska.edu/products-overview/
- GCOV product details: https://nisar-docs.asf.alaska.edu/gcov/
- NISAR naming convention: https://nisar-docs.asf.alaska.edu/naming-conventions/
- HDF5 data structure: https://nisar-docs.asf.alaska.edu/data-format/
- ASF Search NISAR examples: https://nisar-docs.asf.alaska.edu/asf-search/

## 2. GCOV HDF5 paths

Expected groups:

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

Only real diagonal covariance terms are accepted as backscatter power. Off-diagonal covariance terms are complex-valued and must not be treated as a simple intensity layer. Products need not contain every possible term.

## 3. Units and conversions

GCOV diagonal covariance terms represent gamma-naught power (linear scale). Decibels are:

    power_db = 10 * log10(power_linear)

If sigma-naught is required, use the product-provided RTC gamma-to-sigma factor as defined by the product specification. Do not relabel gamma-naught as sigma-naught.

## 4. Scene identity and maturity evidence

A GCOV product name follows the single-acquisition convention:

    NISAR_IL_PT_GCOV_CYL_REL_P_FRM_MODE_POLE_S_StartDateTime_EndDateTime_CRID_A_C_LOC_CTR.EXT

RiverShift extracts and records:
- Instrument band / processing level (for example L2 or S2).
- Processing type (PR, UR or OD).
- Mission cycle and relative orbit.
- Orbit direction, frame number, acquisition mode and polarization mode.
- Source mode, acquisition start/stop and CRID.

The catalogue response keeps:
- requested_maturity_filter: the filter submitted to ASF.
- data_maturity: actual per-product maturity only when ASF reports it.
- maturity_evidence: whether the value comes from product metadata or only from the query filter.

A query filter is not copied into the product's actual metadata field. The stack gate requires one consistent maturity evidence level and does not combine BETA with PROVISIONAL.

## 5. Grid / area contract

The source coordinate arrays define pixel-centre positions. CRS is resolved from the projection grid-mapping dataset and its EPSG/WKT/CF attributes. Pixel area is derived from x/y coordinate spacing and projected CRS axis-unit conversion factors; it is not hard-coded to 100 m² or 10 m × 10 m.

Before pixel-wise change detection, scenes must share:
- instrument band, frequency and covariance term,
- compatible processing/maturity identity (including CRID),
- same CRS and raster dimensions,
- matching x/y coordinate arrays / origin,
- documented resampling policy if exact grids differ.

Current stack validator rejects grid differences; it does not silently resample. If a resampling policy is introduced later, it requires a separate method README and tests. Categorical masks must use nearest-neighbour; continuous backscatter resampling must be documented independently.

## 6. Catalogue query contract

ASF Search supports NISAR discovery using asf_search with dataset=NISAR, processingLevel=GCOV, dataMaturity=PROVISIONAL or BETA, an AOI WKT, an observation date range and a bounded result count.

Catalogue discovery is metadata-only. Search results are not data downloads and do not constitute scientific eligibility.

## 7. Current output contracts

### Open-water classification
- water_mask: Boolean [y, x].
- valid_mask: Boolean [y, x].
- threshold_db: threshold applied to gamma0 dB.
- method: Otsu or fixed.
- counts of valid and candidate pixels.

### Event inundation
- newly_inundated_mask: event water and not baseline water, restricted to common valid pixels.
- baseline/event/new inundated area in km².
- percent water-area change; null when baseline area is zero.

### Persistent morphology candidates
- multiple post-event water masks [time, y, x].
- pre-event validity mask and minimum valid post-event observation count.
- per-pixel post-event water fraction.
- erosion and deposition candidate masks/areas.
- no causal attribution.

## 8. No-data and uncertainty

- Invalid data must remain invalid.
- A pixel without valid pre-event state or sufficient post-event observations cannot confirm persistence.
- A candidate is not a validated erosion/deposition claim.
- A result missing source provenance is not eligible for publication.
- All dates in reports must be UTC with timezone context.
