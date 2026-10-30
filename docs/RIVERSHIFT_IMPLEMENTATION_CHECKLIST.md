# RiverShift implementation checklist

This is the living acceptance checklist for the RiverShift owner. A checkbox is marked complete only when the linked artefact or real observation exists. A script or passing synthetic test does not count as a completed real-world science result.

## A. Product and architecture

- [x] Rename Flood engine card to RiverShift.
- [x] Add the Flood & river change monitoring descriptor.
- [x] Keep the engine marked PILOT rather than claiming full operational readiness.
- [x] Add a public /river-shift workspace route.
- [x] Keep the existing Landslide GUNW/GOFF workflow separate.
- [x] Document module architecture and component boundaries.
- [x] Document challenge scorecard criteria as acceptance requirements.

Evidence:
- Frontend/src/data/engineData.ts
- Frontend/src/pages/RiverShiftPage.tsx
- docs/RIVERSHIFT_ARCHITECTURE.md
- docs/RIVERSHIFT_SCORING_ACCEPTANCE.md

## B. NISAR catalogue and data preparation

- [x] Add a read-only NISAR GCOV catalogue API.
- [x] Add a command-line ASF GCOV discovery script.
- [x] Preserve actual granule names, acquisition dates, orbit/frame metadata and maturity where available.
- [x] Add exact-product download with ASF host validation and checksum receipt.
- [x] Inspect native GCOV HDF5 subdatasets and available diagonal terms.
- [x] Export a selected covariance term to an AOI-clipped COG.
- [x] Document GDAL 3.13+, WGS84 AOI and gamma0 power contracts.
- [ ] Select the final Jamuna/Sirajganj study AOI and commit its reviewed GeoJSON.
- [ ] Query ASF and save an actual catalogue manifest for the selected AOI.
- [ ] Confirm at least three comparable acquisitions exist for one event.
- [ ] Confirm same maturity, frequency, diagonal term, orbit direction, relative track, frame, mode and compatible incidence geometry.
- [ ] Confirm product coverage overlaps the entire analysis AOI, not just a corner.
- [ ] Record product IDs, URLs, dates, version/CRID, sizes, maturity and SHA-256 receipts.
- [ ] Download and archive selected GCOV files outside Git.

Evidence expected:
- data-audit/study_area.geojson
- data-audit/gcov_catalogue.json
- data-audit/acquisition_timeline.csv
- data-audit/feasibility_report.md
- per-product download receipts

## C. Flood inundation analysis

- [x] Add three-date open-water screening.
- [x] Add linear power to dB conversion with 10 log10.
- [x] Add common grid/CRS and NoData checks.
- [x] Add newly water-covered area calculation.
- [x] Add optional permanent-water mask exclusion.
- [x] Add raster, GeoJSON and JSON outputs.
- [x] Add a scientific README and synthetic regression tests.
- [ ] Decide the real flood event using FFWC station records.
- [ ] Select the satellite acquisition closest to the observed event peak.
- [ ] Reproject/resample all dates onto one documented common metric grid.
- [ ] Calibrate the water threshold against independent reference samples.
- [ ] Inspect flooded vegetation and other high-backscatter flood signatures.
- [ ] Run analysis on real NISAR GCOV inputs.
- [ ] Export the true water masks and new-water polygons.
- [ ] Record actual flood metrics with dates, units, threshold and warnings.
- [ ] Validate the flood mask with independent Sentinel-2 or field/reference data.

## D. River morphology and bankline migration

- [x] Add two-post-observation persistence screening for erosion candidates.
- [x] Add two-post-observation persistence screening for deposition candidates.
- [x] Add candidate area and symmetric boundary-distance proxy.
- [x] Add signed bankline measurement along user-oriented transects.
- [x] Require WGS84 GeoJSON inputs and project them into a declared metric CRS.
- [x] Reject ambiguous transect/bankline intersections.
- [x] Add an individual scientific README for morphology and transects.
- [x] Add synthetic transect tests.
- [ ] Digitize and independently review pre/post banklines using one explicit bankline definition.
- [ ] Decide whether the target boundary is the waterline, active-channel edge or outer channel belt.
- [ ] Build and review perpendicular transects with consistent start/end direction.
- [ ] Measure real bankline displacement using the declared positive direction.
- [ ] Check seasonal water-level differences before interpreting shoreline movement as geomorphic change.
- [ ] Review braided channel intersections and invalid transects.
- [ ] Confirm erosion/deposition polygons against optical imagery or independent mapping.
- [ ] Report migration as a two-date net movement, not a long-term forecast.

## E. Scientific validation and evidence

- [x] Add confusion matrix and metrics code.
- [x] Add accuracy, precision, recall, specificity, F1, IoU, kappa and area-bias.
- [x] Require reference source, date and production method in validation reports.
- [x] Add a README and synthetic tests.
- [ ] Create an independent reference water mask for the selected real event.
- [ ] Document optical cloud/shadow masking and acquisition-date difference.
- [ ] Use spatially separated validation samples where possible.
- [ ] Generate a real confusion matrix and validation report.
- [ ] Document uncertainties, class imbalance, false positives and missed flooded vegetation.
- [ ] Have a team member independently review methods and outputs.
- [ ] Do not publish any accuracy or impact figure without evidence.

## F. Frontend and user experience

- [x] Add public RiverShift workspace and ASF catalogue discovery UI.
- [x] Show catalogue-only status separately from scientific results.
- [x] Add JSON/GeoJSON result import.
- [x] Display provenance, metrics and scientific warnings.
- [x] Add satellite map layer for imported GeoJSON when Google Maps is configured.
- [x] Add route and manifest tests.
- [ ] Configure the public Vercel map key and API URL.
- [ ] Configure Render CORS to allow the deployed frontend origin.
- [ ] Import real NISAR-derived results and verify each layer's geographic alignment.
- [ ] Add before/during/after layer controls and an observation timeline.
- [ ] Add a legend for water coverage, erosion candidates, deposition candidates and bankline/transect data.
- [ ] Verify keyboard/touch responsiveness and judge-friendly empty/error states.
- [ ] Add a one-click sample workflow only after a real, openly shareable case study exists.

## G. Cloud processing and persistence

- [x] Reuse the existing FastAPI/worker/Drive architecture as the documented target design.
- [x] Keep Earthdata and server keys out of VITE_ variables.
- [ ] Design the RiverShift job request/result contract.
- [ ] Add a dedicated Supabase migration for RiverShift jobs and result manifests.
- [ ] Apply the migration to the correct active Supabase project after verifying project identity and backup.
- [ ] Add owner-scoped backend endpoints and state transitions.
- [ ] Add a separate GCOV GitHub Actions worker; do not call the Landslide GUNW/GOFF workflow for GCOV.
- [ ] Add signed callbacks, idempotency and resource limits.
- [ ] Upload and verify private result bundles.
- [ ] Add result retrieval and expiration/retention rules.
- [ ] Test staging end-to-end before production deployment.

## H. NASA Space Apps scoring evidence

- [x] Identify the challenge: 2026 NASA Space Apps Challenge — Dancing with the SARs.
- [x] Map the 11 scored criteria to evidence in docs/RIVERSHIFT_SCORING_ACCEPTANCE.md.
- [x] Make the repository open-source/public (verify signed-out access before submission).
- [ ] Demonstrate measurable impact with a real event and affected land-cover context.
- [ ] Demonstrate creative, intuitive interactive time-series storytelling.
- [ ] Demonstrate scientific validity using real independent validation.
- [ ] Demonstrate relevance by making NISAR GCOV the actual primary input, not a decorative reference.
- [ ] Complete project page, team contribution details, demo and repository links.
- [ ] Collect truthful team collaboration evidence (reviews, commits, role descriptions).
- [ ] Verify any women participation bonus against actual registered team composition; never infer from source code.

## Final release gate

Do not mark RiverShift as final-judge-ready until:
1. Real GCOV coverage is confirmed for the final AOI.
2. At least three comparable acquisitions are processed.
3. Flood and morphology outputs are generated from real data.
4. At least one independent validation report exists.
5. The deployed UI presents the real case study with provenance, legend and limitations.
6. Repository and official NASA project page are open, complete and reproducible.
