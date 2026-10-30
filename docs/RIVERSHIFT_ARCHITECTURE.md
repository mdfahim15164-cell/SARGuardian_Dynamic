# RiverShift architecture

## Product goal
RiverShift is an independent surface-change engine inside SARGuardian for mapping NISAR-observed river/flood changes. It targets the NASA Space Apps 2026 challenge “Dancing with the SARs”.

## Module boundaries
- Existing Landslide: preserve its GUNW/GOFF displacement processing and routes.
- RiverShift: separate GCOV catalogue, product preparation, intensity-based water classification, morphology screening, validation and results presentation.
- Shared platform: Firebase authentication (where required), FastAPI, Vercel frontend, Render API deployment, GitHub repository and existing private storage patterns.

## Data flow
1. User chooses a WGS84 AOI and acquisition interval.
2. Frontend calls the read-only GCOV catalogue endpoint.
3. Backend queries ASF DAAC for dataset=NISAR and processingLevel=GCOV.
4. User reviews granule dates, maturity, orbit, frame, polarization and coverage.
5. Local CLI or a future isolated GitHub Actions worker downloads the exact selected HDF5 products.
6. GDAL inspects/extracts the required diagonal GCOV layers and clips them to the AOI.
7. Scientific scripts produce GeoTIFF masks, GeoJSON polygons and JSON result manifests.
8. Reviewed banklines and transects can be measured by the signed migration script.
9. Frontend imports and visualizes the real JSON/GeoJSON outputs.

## Existing vs new capability
Existing platform components include React/Vite, FastAPI, Firebase identity, Supabase job metadata, GitHub Actions, Google Drive artifact storage, and NISAR GUNW/GOFF workflows. Existing GUNW/GOFF workflows are not repurposed as GCOV water classification.

New RiverShift deliverables in this PR:
- Separate read-only GCOV catalogue endpoint.
- GCOV manifest, exact download, HDF5 inspection and AOI export scripts.
- Flood inundation screening.
- Persistent erosion/deposition candidate screening.
- Binary validation metrics.
- Signed transect-based bankline displacement measurements using independently digitised banklines and user-oriented cross-sections.
- Separate public RiverShift workspace route and scientific-report import UI.
- Scientific READMEs and automated tests.

Not implemented in this milestone:
- Automated cloud download/processing dispatch for GCOV.
- A new Supabase RiverShift job table/migration.
- Private artifact upload/retention for RiverShift.
- Live NISAR AOI imagery basemap.
- Automated NISAR bankline extraction and active-channel belt delineation; transect measurement requires reviewed input lines.
- Operational flood depth or risk forecasting.

## Why the processing split matters
GCOV is the Level-2 geocoded polarimetric covariance/backscatter product, suitable for intensity and inundation screening. GUNW is an unwrapped interferometric displacement product, while GOFF contains pixel offsets. Reusing a displacement algorithm for water detection would be scientifically invalid.

## Frontend contract
Route: /river-shift.
- Live ASF catalogue search returns only metadata.
- Results explorer loads script-produced result JSON and GeoJSON.
- Every metric is presented with source provenance, QA status and warning text.
- No default/example metric is shown as measured data.
- GeoJSON coordinate preview is not a basemap; final map integration should use a genuine geographic map projection and base layer.

## Backend contract
POST /api/river-shift/catalog/search is read-only. It does not download imagery, create jobs, or run analysis. Its response explicitly carries:
- mode=catalogue_only
- data_downloaded=false
- scientific_analysis_performed=false
- exact product granule names and ASF metadata
- maturity and warnings.

## Security
- Earthdata credentials are used only by a local trusted process or server-side worker.
- Do not store secrets in VITE_* variables.
- Do not log tokens or product auth headers.
- Existing Landslide callback signature and owner checks remain unchanged.
- Do not enable public storage for result HDF5 or private user AOIs.

## Acceptance definition
A milestone is complete only when the associated README is satisfied, automated tests pass, provenance is retained, scientific limitations are surfaced, and the frontend never presents a catalogue response as a scientific result.
