# RiverShift · NASA Space Apps scorecard acceptance matrix

This document turns the supplied judging score sheet into verifiable project evidence. It is an engineering acceptance plan, not a promise of a judging score.

## Headline criteria (1–5): 100 points

### 1. Impact (1–20)
Evidence:
- AOI-specific floodwater expansion and persistent river-change maps.
- Area measurements with units and uncertainty/validation context.
- Overlay of affected agricultural/built-up land only when a trusted ancillary dataset exists.
Acceptance:
- A real documented study event is analysed.
- Results distinguish temporary water coverage from persistent channel/land changes.
- No household, population or damage claim is inferred from backscatter alone.

### 2. Creativity (1–20)
Evidence:
- River timeline, before/during/after comparison, erosion/deposition layers and change hotspot inspection.
- One interactive workflow that connects archive discovery to reproducible scientific reports.
Acceptance:
- Every map layer has a clear legend and time label.
- User can compare multiple observation dates.
- The project communicates the river as a changing system, not only a static flood polygon.

### 3. Validity (1–20)
Evidence:
- Per-script and per-algorithm scientific README, methods, assumptions, tests, validation report, reference source and limitations.
- Signed bankline chainage displacement along reviewed transects, with a declared sign convention and invalid-intersection handling.
- Synthetic algorithm tests plus independent real-world validation.
Acceptance:
- Time-series inputs meet acquisition comparability requirements.
- Signed bankline displacement uses reviewed WGS84 GeoJSON banklines, a projected metre analysis CRS, a declared transect direction, and rejects ambiguous multiple intersections.
- CRS, grid, units, maturity, frequency and polarization are recorded.
- Report confusion matrix, precision, recall, F1 and IoU.
- Label candidate morphology changes as candidates until independently corroborated.
- No unverified accuracy or causal claim is published.

### 4. Relevance (1–20)
Evidence:
- NASA-ISRO NISAR GCOV is the primary measured radar dataset.
- Mission, instrument, product, granule IDs, dates, frequency, polarization and maturity are displayed.
- The README explains why GCOV is used and why GUNW/GOFF are not substituted.
Acceptance:
- Actual NISAR GCOV imagery contributes directly to the output.
- Satellite metadata and official product documentation are cited.
- Any Sentinel-2, FFWC or land-cover data are clearly marked as supporting/validation data.

### 5. Presentation (1–20)
Evidence:
- RiverShift public workspace, clear study controls, workflow status, map legend, result metrics and readable provenance/limitations.
- Clear story: what changed, where, when, how measured and how reliable.
Acceptance:
- A judge can follow the demo without reading source code.
- Empty/no-data/error states are informative.
- The UI distinguishes catalogue results from completed scientific analysis.
- One documented real case study can be reproduced.

## Supporting criteria (6–8): 15 points

### 6. Teamwork (1–5)
Evidence to collect:
- Named contributor roles in the project page/README.
- Real commit history, code reviews, pull requests and documented scientific review.
Acceptance:
- Every claimed team contribution is real and attributable.
- Do not invent contributor names or credit.

### 7. User experience (1–5)
Evidence:
- Public RiverShift route, labelled inputs, sensible defaults, progress/errors, clear units, empty states and keyboard-usable controls.
Acceptance:
- A first-time judge can discover data and understand what the button does.
- Catalogue discovery is not presented as flood processing.
- Scientific results can be inspected without editing code.

### 8. NASA data usage (1–5)
Evidence:
- NISAR GCOV products from ASF DAAC.
- Supporting source citations for ASF, Sentinel-2 and/or Bangladesh FFWC where actually used.
Acceptance:
- NASA-ISRO NISAR is the primary analysed dataset, not a decorative logo.
- Other-agency/third-party data are explicitly credited and their role is described.
- Product URLs, IDs, maturity and access dates are retained.

## Binary criteria (9–11): 3 points

### 9. Challenge category identified (0 or 1)
- Explicitly identify “2026 NASA Space Apps Challenge — Dancing with the SARs” on the app, project README and submitted project page.

### 10. Repository access (0 or 1)
- Make the GitHub repository public and verify that a signed-out judge can open it.
- Include reproduction instructions and licences for all added source/data assets.

### 11. Project page complete (0 or 1)
- Complete and submit the official NASA Space Apps project page.
- Include challenge category, problem, solution, data, methods, team, impact, demo and repository links.

## Women participation bonus (+5%)
- The score sheet grants a 5% bonus to teams with one or more women members.
- Only claim it if the actual registered team composition meets the event rule; the project code cannot establish team composition.

## AI judge evidence package
Provide these files/links in the repository:
- docs/RIVERSHIFT_ARCHITECTURE.md
- docs/RIVERSHIFT_SCORING_ACCEPTANCE.md
- docs/RIVERSHIFT_RESEARCH_DECISIONS.md
- tools/river_shift/README.md
- README_01 through README_08, each immediately preceding its script's task.
- One scientific README for every calculation module, including `river_shift/README_06_transects.md`.
- Reproducible commands, tests, real case-study outputs, provenance manifest and validation report.
- README_08 for signed bankline migration, plus a module README for transect calculations.

## Final pass/fail gate
Do not mark RiverShift ready for final judging until:
1. A real AOI and real NISAR GCOV products are confirmed.
2. At least three comparable acquisition dates are downloaded and processed.
3. Flood and morphology outputs are produced from the real products.
4. Independent reference validation is documented.
5. Where bankline movement is claimed, dated banklines and transects are independently reviewed and signed displacement results are reproducible.
5. The UI shows the real outputs with provenance and caveats.
6. Public repository and official project page are complete.
