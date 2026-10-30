# RiverShift — System Architecture

**Product:** RiverShift — Flood & River Change Intelligence  
**Parent application:** SARGuardian Dynamic  
**NASA Space Apps 2026 challenge:** Dancing with the SARs  
**Challenge category:** Earth Science / Earth's surface

## 1. Product intent

RiverShift uses repeat-pass NISAR radar observations to help users inspect and quantify changes in river systems. The first study is proposed for a controlled reach of the Jamuna River near Sirajganj, subject to a successful NISAR catalogue coverage audit.

The first release separates two phenomena:

- **Event inundation:** temporary expansion of water coverage during a flood.
- **Persistent river morphology candidates:** land-to-water and water-to-land transitions that remain after water levels recede.

This prevents peak-stage river expansion from being mislabeled as permanent channel migration.

## 2. Logical architecture

    User / Reviewer
        |
    React + TypeScript RiverShift workspace (/river-shift)
        |
    Firebase-authenticated FastAPI endpoint
        |
    ASF NISAR GCOV catalogue (metadata-only in current milestone)
        |
    Scene manifest + granule identity parser
        |
    Comparable-scene metadata gate
        |
    GCOV HDF5 download worker (planned)
        |
    GCOV reader -> CRS/coordinates/units/quality checks
        |
    Exact-grid compatibility gate
        |
    Open-water candidate classifier
        |--------------------------|
        |                          |
    Event inundation        Persistent morphology
    area accounting         erosion/deposition candidates
        |                          |
        |---- independent validation / provenance ----|
                              |
             GeoTIFF/COG + GeoJSON + JSON manifest
                              |
            Private result storage + Supabase job state
                              |
                       RiverShift UI

The current branch implements the authenticated metadata search and independent science foundations. It does not yet execute the end-to-end processing chain on real NISAR scenes.

## 3. Existing infrastructure reuse

| Existing SARGuardian component | RiverShift use | Rule |
|---|---|---|
| React/Vite frontend | New RiverShift route and workspace | Do not change Landslide UI behavior |
| Firebase Authentication | User identity | Reuse existing ID-token verification |
| FastAPI | RiverShift catalogue endpoint | Separate router/module |
| Supabase | Future durable RiverShift job metadata | New migration; do not alter Landslide job meaning |
| GitHub Actions | Future GCOV worker | New workflow and isolated concurrency group |
| Private Google Drive result retention | Future large result packages | Keep existing owner-scoped access controls |
| Vercel | Frontend deployment | Do not add secrets to browser variables |
| Render | Existing API service where configured | Reuse server-side configuration only |

## 4. Scientific processing architecture

### 4.1 Data discovery

Use ASF asf_search with dataset=NISAR, processingLevel=GCOV, explicit date window, AOI and one dataMaturity filter.

The catalogue endpoint is metadata-only. It returns the original granule name and the metadata reported by ASF. The query's requested maturity filter is kept separate from an individual product's reported maturity. If per-product maturity is absent, it remains null.

A source manifest must eventually retain:
- Granule name and product ID.
- Observation start/stop times in UTC.
- Instrument band and product processing level.
- Cycle and relative orbit, direction and frame.
- Acquisition mode and polarization mode.
- Per-product maturity and maturity-query evidence.
- CRID / processing baseline.
- Frequency, covariance term, product URL and source file size where available.
- AOI WKT hash and request parameters.

### 4.2 Scene comparability

The current scene selector groups products by maturity evidence, instrument band, processing type, relative orbit, direction, frame, acquisition mode, polarization mode, source mode and CRID. It records mission cycle but does not use cycle number as the sole ground-track identity.

Passing this metadata gate only means the group is eligible for HDF5 grid checks. It does not itself prove that the geocoded grids match.

### 4.3 Product reading and grid gate

Read a documented real-valued GCOV diagonal covariance term (e.g. VVVV) and same-grid x/y coordinate arrays and projection metadata. The reader resolves CRS from EPSG/WKT/CF metadata and does not assume a Bangladesh UTM zone or fixed pixel size.

The grid gate requires matching frequency, covariance term, shape, CRS and coordinate arrays before pixel-wise temporal comparison. It refuses silent resampling.

### 4.4 Water classification

Convert positive linear gamma-naught power to dB and produce open-water candidates using a declared Otsu or fixed threshold. Keep the threshold, valid-pixel mask and provenance.

This baseline is not a complete flooded-vegetation classifier. Radar double-bounce returns can make some flooded vegetation bright. Local reference calibration and additional contextual features are required.

### 4.5 Inundation

    newly_inundated = event_water AND NOT baseline_water

The baseline should be a stable or persistent water reference where possible. Report baseline water, event water and newly inundated area separately. A peak event scene alone does not establish the flood peak or water depth.

### 4.6 Persistent morphology candidates

Use one pre-event reference and at least two comparable post-recession observations. A candidate must persist across the declared fraction of valid post-event observations.

- Pre-event land + persistent post-event water = erosion candidate.
- Pre-event water + persistent post-event land = deposition candidate.

These are candidate transitions until independently checked under comparable hydrological conditions.

## 5. Deployment boundary

Canonical science code belongs in Backend/science_adapter/river_shift/. Worker-facing scripts belong in tools/river_shift/. The independent science dependencies are listed in Backend/requirements-river-shift.txt.

Implemented in this branch:
- Firebase-authenticated GCOV catalogue API.
- RiverShift frontend route and catalogue search workspace.
- GCOV HDF5 reader and CRS handling.
- Scene identity and comparable-stack metadata gate.
- Candidate open-water classification, event area accounting and persistent-change calculations.
- Confusion matrix / threshold sensitivity helpers.
- Single-scene candidate GeoTIFF export.
- Synthetic unit tests and task-specific READMEs.

Not implemented yet:
- Secure GCOV download and checksum worker.
- AOI-windowed/chunked HDF5 reading.
- Documented use of the GCOV mask layer.
- Durable Supabase RiverShift jobs and GitHub Actions dispatch.
- End-to-end result bundle delivery.
- Real-scene validation and interactive analysis layers.

## 6. Failure and safety controls

- No result without a source-product manifest.
- No mixing of BETA and PROVISIONAL products within one comparison stack.
- Do not treat query maturity filter as a per-product reported field.
- Reject unsupported covariance terms and missing coordinate metadata.
- Do not treat no-data as dry land.
- Require same-grid alignment before pixel-wise subtraction.
- Record algorithm settings, quality policy and valid-pixel rules.
- Never expose Earthdata, GitHub, Firebase Admin or Supabase server secrets to the browser.
- Mark results as candidate / provisional until independent validation is complete.
- UI must not present candidate layers as public flood warnings.

## 7. Next engineering increments

1. Complete Jamuna AOI and actual GCOV data-availability audit.
2. Implement secure GCOV download and checksum/source manifest.
3. Decode GCOV mask / quality information from the product specification.
4. Add AOI-windowed/chunked reading and production COG export.
5. Run event inundation and persistent morphology on real, compatible NISAR scenes.
6. Add bankline extraction and transect displacement with its own README/tests.
7. Add channel-width / active-channel-belt measurement with its own README/tests.
8. Build independent reference labels, sensitivity experiments and real-scene validation report.
9. Add Supabase jobs, GitHub Actions dispatch and private result retrieval.
10. Complete the final interactive map, story and NASA project page.
