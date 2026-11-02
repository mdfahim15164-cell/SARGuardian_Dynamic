# Sirajganj–Kazipur Jamuna candidate AOI

## Approval status

**AOI: CANDIDATE_NOT_APPROVED. Event timing: NOT_APPROVED.** The broad rectangle is for catalogue feasibility only. It is not a final scientific study boundary, active-channel corridor, bankline, flood extent, administrative boundary or field-validated area.

## Candidate geometry

```text
POLYGON ((89.62 24.43, 89.78 24.43, 89.78 24.68, 89.62 24.68, 89.62 24.43))
```

The archived audit calculates 449.342 km² in UTM zone 45N (EPSG:32645). The candidate rectangle contains two official BWDB historical water-level station anchors: Sirajganj SW49 at 24.4685° N, 89.7196° E and Kazipur SW49A at 24.6698° N, 89.6491° E. BWDB's availability summary lists both station series from 2015 through 31 January 2026. Its station danger-level table lists 13.35 mPWD for SW49 and 15.24 mPWD for SW49A. These references anchor the search window; they do not establish a suitable corridor boundary.

## Live catalogue evidence captured 2026-11-02

The official ASF/CMR query covered 17 June–31 October 2026, PROVISIONAL GCOV, over the candidate rectangle. It returned 34 product records. The strongest product-level review group contains ten dates on ascending relative orbit 069/frame 014, mode 4005, DHDH, acquired single-mode, CRID P05023, near-real-time orbit accuracy, full frames and JPL processing. The requested Frequency-A HHHH term is encoded as available. For mode 4005, Frequency A uses 40 MHz and has an expected 10 m GCOV pixel spacing. Every selected date has 100% geometric footprint coverage of the candidate AOI.

The ten dates are 18 June, 30 June, 12 July, 24 July, 17 August, 29 August, 10 September, 22 September, 4 October and 16 October 2026. The NISAR guide records an instrument data gap from 27 July 22:03:25 UTC through 10 August 00:55:27 UTC, which explains the gap between 24 July and 17 August.

These are catalogue and footprint facts only. They do not establish valid-pixel coverage, HDF5 dataset presence, exact grid compatibility, a flood extent, river-bank migration, or a flood date. See the [CMR manifest](nisar_gcov_candidate_manifest_2026-11-02.json) and [product-level audit](nisar_gcov_candidate_audit_2026-11-02.json). A selected product URL redirected to Earthdata Login; no authenticated session was available, so no product bytes or HDF5 datasets were inspected.

## Event timing gate

The September acquisitions are candidate observations, not a verified flood peak. BWDB's published availability summary lists the Sirajganj and Kazipur series through 31 January 2026, and the FFWC observed-water-level page returned “No observed water level data available” during this review. Therefore the event date, stage and peak are **NOT_APPROVED** until the original official station observations covering the NISAR acquisition dates are retrieved and reviewed. Do not select a “during” image based on a news headline or catalogue date alone.

## Required before scientific analysis or judging claims

1. Have the science team approve a river-corridor AOI and document the boundary definition.
2. Retrieve official BWDB/FFWC water levels for the acquisition window and choose stage-comparable dates.
3. Authenticate with NASA Earthdata Login and download the exact same-frame product group; retain IDs and SHA-256 receipts.
4. Inspect each HDF5 product and verify the selected Frequency-A HHHH dataset and matching mask.
5. Compare CRS, dimensions and affine grids; quantify valid-mask coverage for each date and review incidence geometry.
6. Process flood expansion separately from persistent river-bank/land transitions.
7. Compare the water classification against an independent dated reference and independently review any banklines/transects.
8. Keep all outputs PROVISIONAL until review evidence, provenance and uncertainty are complete.

## Authoritative sources

- [NISAR GCOV product guide](https://nisar-docs.asf.alaska.edu/gcov/)
- [NISAR availability, CRID and data-gap notes](https://nisar-docs.asf.alaska.edu/availability-overview/)
- [NASA Earthdata access and authentication guide](https://nisar-docs.asf.alaska.edu/earthaccess/)
- [BWDB water-level station/data availability](https://www.hydrology.bwdb.gov.bd/includes/water_level_data_available_print.php)
- [BWDB Brahmaputra–Jamuna station danger levels](https://en.bwdb.gov.bd/archive/pdf/6591.pdf)
- [FFWC observed water-level page](https://ffwc.gov.bd/app/observed-water-level)
