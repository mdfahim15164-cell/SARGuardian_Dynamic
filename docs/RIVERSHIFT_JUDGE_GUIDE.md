# RiverShift judge guide

## What the module does

RiverShift is the NISAR GCOV river and flood-change module in SARGuardian Dynamic. It separates three questions that are often conflated:

1. **Flood expansion:** where a comparable event-period observation has new open-water candidates relative to a pre-event observation.
2. **Persistent river/land transition:** which land-to-water and water-to-land changes persist across two post-event observations.
3. **Bank migration:** how independently reviewed banklines move along fixed, oriented transects.

Flood expansion and persistent morphology use different inputs, definitions and outputs. The morphology boundary-distance statistic is an unsigned screening distance; signed movement comes only from the separate transect tool. Neither algorithm identifies flood causation by itself.

## Follow the evidence chain

1. **Discover:** query the official NASA CMR/ASF DAAC NISAR L2 GCOV collection.
2. **Screen:** group by maturity, direction, relative orbit, NISAR frame, bandwidth, polarization, processing type, observation source, CRID, orbit accuracy, frame coverage and processing center. Check the requested frequency/diagonal term against encoded mode metadata and measure AOI footprint coverage.
3. **Inspect and prepare:** authenticate to download the exact product, inventory HDF5 layers, select a real-valued diagonal GCOV covariance term, export the matching frequency mask, exclude invalid samples, and preserve SHA-256 provenance. Download receipts bind local identity and bytes for reproducibility; NASA/ASF does not sign these local receipt files.
4. **Process separate outputs:** calculate flood water candidates separately from persistent erosion/deposition candidates. Require exact raster-grid agreement and record input dates, units, masks and checksums.
5. **Validate and review:** compare a binary prediction with a dated independent reference, report the confusion matrix and scores with spatial block-bootstrap intervals, and review any bankline geometry and declared measurement uncertainty.
6. **Release:** the dashboard shows metric values only for reports with `release_status: VERIFIED`, complete provenance and an evidence-bearing review record. A change polygon is drawn only when its file SHA-256 matches one of the GeoJSON output digests in that report. Generated analysis reports remain `PROVISIONAL`. The uploaded report's reviewer record is a documented human assertion; the browser does not cryptographically authenticate reviewer identity.

## What has been verified for the candidate study

The archived live CMR query returned **34 catalogue records** for the candidate Sirajganj–Kazipur rectangle from 17 June through 31 October 2026, filtered to PROVISIONAL products. The top candidate group has **10 acquisition dates**, all with **100% geometric footprint coverage** of the rectangle: 18 June, 30 June, 12 July, 24 July, 17 August, 29 August, 10 September, 22 September, 4 October and 16 October.

That group is ascending relative orbit 069, NISAR frame 014, 4005 bandwidth mode, DHDH dual polarization, acquired single-mode, CRID P05023, near-real-time orbit accuracy, full frame coverage and JPL processing. For Frequency A, the encoded dual-HH/HV mode supports the HHHH diagonal term; the requested term has **not** yet been verified inside any selected HDF5 file. For mode 4005, Frequency A is 40 MHz with expected 10 m GCOV posting. The paired Frequency B is 5 MHz with expected 80 m posting, so those grids must not be mixed.

These catalogue records are availability and geometric-coverage evidence only. The 100% number is footprint intersection with a candidate rectangle. It says nothing about valid-sample-mask coverage, sample counts, exact grids, calibration values, water class, flood extent or bankline change. The official NISAR guide says GCOV diagonal terms are real-valued radiometrically terrain-corrected backscatter and that each frequency has a `/mask` layer describing the adaptive multi-looking ensemble. RiverShift exports one frequency/term and applies the matching mask.

## AOI and event decision

The rectangular AOI remains **CANDIDATE_NOT_APPROVED** pending team review of a river-corridor boundary. BWDB station records place historical Sirajganj SW49 and Kazipur SW49A anchors inside it. BWDB's published data-availability page lists both historical series only through 31 January 2026; the FFWC observed-water-level page returned no current observed data in this review. The 2026 event date, stage and flood peak therefore remain **NOT_APPROVED**. September NISAR acquisitions are potential observations, not evidence that one is the flood peak.

## Validation and uncertainty

- Flood and morphology reports contain five fixed offsets around the selected dB threshold. This deterministic sensitivity is method robustness, not a confidence interval.
- Classification validation computes TP/TN/FP/FN, accuracy, precision, recall, specificity, F1, IoU, kappa and area bias. A reproducible block bootstrap resamples spatial blocks (default 64 pixels) and reports percentile intervals only when at least 20 blocks are available. The intervals describe spatial-block variability at that scale; they exclude reference-label error and other systematic uncertainties. Validation provenance is complete only when the prediction checksum matches a mask output in its adjacent RiverShift report and that report carries the source granule IDs and checksums.
- Transect migration can report per-transect approximate 95% intervals when both bankline position standard deviations are supplied. These intervals assume independent isotropic Gaussian errors and exclude stage, geolocation, transect placement and bankline-definition uncertainty. Without both sigmas, uncertainty is `NOT_QUANTIFIED`.
- A declared reference or a passing synthetic test does not establish independent real-world validation. Human review must confirm reference independence and suitability.

## Current blockers

1. NASA Earthdata Login is required to retrieve product bytes. A selected product request redirected to the login host; no local authenticated session was available, so no HDF5 files were downloaded or inspected.
2. The candidate AOI requires a team-approved river-corridor boundary.
3. Official 2026 gauge observations are needed to select stage-comparable before/event/after dates.
4. Real flood classification, morphology outputs, independent reference validation and reviewed bankline migration remain to be produced.

No flood area, erosion/deposition area, accuracy value or real bank-migration rate is published by this repository snapshot. The dashboard therefore keeps unverified reports and all unverified GeoJSON off the public metrics/map view.

## Judge walkthrough

1. Configure `VITE_GOOGLE_MAPS_API_KEY` in `Frontend/.env.local` (Google Maps JavaScript API enabled), then restart the frontend. This key is browser-visible and should be restricted to the team's allowed origins.
2. Open `/river-shift`; use **Start drawing** and click the satellite map to outline the candidate AOI. **Finish AOI** creates a closed WGS84 polygon used by the ASF catalogue form. The boundary remains a candidate until the science team approves it.
3. Run `run_water_timeseries.py` with the real comparable acquisitions. Import its `river_shift_timeseries.json` and all report-listed date GeoJSON files. The play control steps between exact observation dates and explicitly does not interpolate daily states.
4. Read the imported report's release status, source granule IDs/checksums, valid-pixel coverage, input checksums, sensitivity scenarios and limitations.
5. Observe that `PROVISIONAL` reports do not display metric cards or draw GeoJSON. The layer must pass the review/provenance gate and exact SHA-256 match.
6. The map legend separates erosion candidates, deposition candidates, and water candidates. These are screening classes, not field-confirmed land loss/accretion or flood causation.
7. Reproduce the synthetic regression suite from `tools/river_shift`; tests verify software behavior only and are not presented as real-world accuracy.
8. Use the archived manifest and audit to inspect the candidate dates, group signature, footprint percentages and explicit non-HDF5 caveat.

## Reproducibility and reference links

- Candidate query and raw metadata: [`data-audit/nisar_gcov_candidate_manifest_2026-11-02.json`](../data-audit/nisar_gcov_candidate_manifest_2026-11-02.json)
- Recomputed group/coverage audit: [`data-audit/nisar_gcov_candidate_audit_2026-11-02.json`](../data-audit/nisar_gcov_candidate_audit_2026-11-02.json)
- AOI and event decision: [`data-audit/README_SIRAJGANJ_CANDIDATE.md`](../data-audit/README_SIRAJGANJ_CANDIDATE.md)
- CLI methods, tests and outputs: [`tools/river_shift/README.md`](../tools/river_shift/README.md)
- Official NISAR GCOV guide: https://nisar-docs.asf.alaska.edu/gcov/
- Official NISAR availability/maturity and instrument data gap: https://nisar-docs.asf.alaska.edu/availability-overview/
- Official BWDB station/data availability: https://www.hydrology.bwdb.gov.bd/includes/water_level_data_available_print.php
- Official BWDB danger-level table: https://en.bwdb.gov.bd/archive/pdf/6591.pdf
- FFWC observed levels: https://ffwc.gov.bd/app/observed-water-level
