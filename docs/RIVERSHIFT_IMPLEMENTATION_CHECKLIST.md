# RiverShift implementation checklist

This checklist is both a work tracker and a code-review acceptance gate. A checked item must be backed by a file, automated test, or real-data evidence. Do not mark a real-science gate complete using synthetic fixtures.

## A. Project and NASA challenge alignment

- [x] Name the engine **RiverShift — Flood & River Change Intelligence**.
- [x] Identify the challenge as **2026 NASA Space Apps — Dancing with the SARs**.
- [x] Identify category as **Earth Science / Earth's surface**.
- [x] Keep RiverShift separate from the existing Landslide/GUNW/GOFF science pipeline.
- [x] Document the scorecard and acceptance evidence in `docs/RIVERSHIFT_SCORECARD_ACCEPTANCE.md`.
- [ ] Complete NASA project page, upload media, add public demo/repository, and submit it (manual team task).
- [ ] Verify the public repository and final deployed demo are accessible without team-only credentials.

## B. Foundation implementation

- [x] Separate FastAPI router for metadata-only GCOV catalogue search.
- [x] Firebase authentication required for catalogue search.
- [x] WGS84 polygon validation and geodesic AOI area limit.
- [x] Explicit single data-maturity selection (PROVISIONAL or BETA).
- [x] GCOV HDF5 diagonal-layer reader.
- [x] Grid coordinate, projection, shape and valid-pixel checks.
- [x] Linear power to dB conversion and Otsu/fixed open-water candidate classifier.
- [x] Event inundation area accounting with common validity mask.
- [x] Multi-date persistent erosion/deposition candidate logic.
- [x] Independent-reference confusion matrix, F1, IoU and threshold sensitivity helpers.
- [x] GeoTIFF candidate-map exporter and JSON sidecar script.
- [x] Scientific README beside each implemented task/script.
- [x] Synthetic software-contract tests for core calculations.
- [x] Dedicated RiverShift frontend route, Firebase gating, catalogue search form and result table.
- [ ] Build/lint/test checks pass on GitHub Actions (pending CI execution for this PR).

## C. Real NISAR data feasibility — not complete until actual catalogue results are saved

- [ ] Define and save the Sirajganj Jamuna AOI polygon with source and coordinates.
- [ ] Run ASF NISAR GCOV search for that AOI and a documented observation window.
- [ ] Save actual returned granule names, acquisition dates, path/frame, direction, maturity, frequency/polarization, CRID and file sizes where provided.
- [ ] Confirm at least one usable pre-event observation and event-time observation.
- [ ] Confirm at least two usable post-recession observations for persistent-change analysis.
- [ ] Confirm products share a compatible processing maturity, CRID, frequency, covariance term, track/frame and comparable acquisition geometry.
- [ ] Select a flood event using independent FFWC observation data; record station, timestamp, datum and source.
- [ ] If Jamuna coverage is insufficient, document the failed feasibility check before selecting a different pilot.

## D. Production scientific processing — not yet complete

- [ ] Implement secure authenticated GCOV file download and checksum verification.
- [ ] Persist an immutable source-product manifest.
- [ ] Implement a comparable-scene stack eligibility gate.
- [ ] Implement AOI-windowed/chunked HDF5 reading for large scenes.
- [ ] Decode product mask/quality information according to the product specification.
- [ ] Implement and test a documented grid-alignment policy.
- [ ] Export AOI-clipped COG/GeoTIFF and GeoJSON layers with CRS, transform and NoData metadata.
- [ ] Generate baseline/event flood extent from real GCOV scenes.
- [ ] Generate persistent erosion/deposition candidates from post-recession scenes.
- [ ] Add bankline extraction and perpendicular transect displacement with a separate methodology and tests.
- [ ] Add channel-width / active-channel-belt measurement with a separate methodology and tests.

## E. Independent validation — must be real data, not synthetic unit tests

- [ ] Create independent reference labels with source, date, resolution, CRS, sampling and interpreter/method.
- [ ] Validate water classification against independent reference pixels/polygons.
- [ ] Report TP, FP, FN, TN, sample count, precision, recall, F1, IoU and accuracy.
- [ ] Run threshold sensitivity analysis and document class imbalance.
- [ ] Inspect errors over flooded vegetation, smooth bare soil, urban surfaces, shadow and wet soil.
- [ ] Validate morphology candidates against later imagery and/or independently digitised banklines.
- [ ] Record all limitations and uncertainty in a real-scene validation report.
- [ ] Only then publish accuracy metrics or claim an observed Jamuna change.

## F. Application integration and presentation

- [x] RiverShift workspace route and guided catalogue-first UI.
- [x] Clearly label catalogue search as metadata-only.
- [x] Keep fabricated flood-area/erosion KPI values out of the page.
- [ ] Add durable RiverShift job records and ownership policies in a new Supabase migration.
- [ ] Add isolated GCOV GitHub Actions worker with signed, ordered completion callback.
- [ ] Reuse private result storage without exposing service credentials.
- [ ] Add before/during/after time slider and separate inundation/morphology layers.
- [ ] Add clear legend, metric definitions, source citations and uncertainty.
- [ ] Add downloadable source manifest, processing parameters, metrics and validation report.
- [ ] Document user instructions and accessibility in the project page.

## G. Team / rubric evidence

- [ ] Team contribution log and meaningful PR reviews (Teamwork).
- [ ] Project story explains impact using verified figures and affected-place context (Impact).
- [ ] Demo shows the distinction between temporary inundation and persistent channel change (Creativity / Validity).
- [ ] NISAR is visible as the primary data source in UI, README and reports (Relevance / NASA data usage).
- [ ] Supporting Sentinel-2 / FFWC sources are cited and not misrepresented as NISAR (NASA data usage).
- [ ] A first-time user can run the guided workflow without technical training (User experience).
- [ ] Public GitHub / demo links verified (Repository access).
- [ ] NASA challenge project page completed and submitted (Project page complete).
- [ ] Women participation bonus eligibility confirmed accurately by the team (bonus).

## Status note

The checked implementation items describe code/docs added to the development branch. They do not imply real NISAR data have been downloaded, a Jamuna event has been analysed, scientific accuracy has been measured, or a production deployment is live.
