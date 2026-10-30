# RiverShift — NASA Space Apps 2026 Scorecard Acceptance Plan

This document translates the supplied judging sheet into engineering and submission evidence. It is an acceptance plan, **not a prediction or guarantee of judging scores**.

## Scoring structure from the supplied sheet

- Criteria 1–5: maximum 100 headline points.
- Criteria 6–8: maximum 15 additional points.
- Criteria 9–11: maximum 3 additional points.
- Maximum before bonus: 118.
- Women participation bonus: +5% on top of aggregate where the team meets the published condition.

## Acceptance matrix

| # | Criterion | Max | What judges need to see | RiverShift acceptance evidence | Owner / state |
|---|---|---:|---|---|---|
| 1 | Impact | 20 | Scale/significance of the problem and reach | Explain river erosion/floodplain exposure; show measured event area and persistent change only after real-data validation; describe how local users can use the results | Team story + validated case study / pending |
| 2 | Creativity | 20 | Originality of idea and execution | Distinguish temporary inundation from persistent morphology; show multi-date river change, bankline transects and interpretable time slider; explain why this combination adds value | RiverShift concept / partial |
| 3 | Validity | 20 | Scientific soundness, feasibility, usability | Product/maturity checks, traceable units and CRS, independent reference labels, confusion matrix, IoU/F1, sensitivity analysis, no-data handling, reproducible tests | Science README + tests + real-scene validation / foundation implemented |
| 4 | Relevance | 20 | Challenge alignment and depth of NASA data use | NISAR GCOV must be the primary analytical input; list actual granules, acquisition dates, L-band frequency, polarization, maturity and processing baseline; use NASA/ASF metadata in every result | GCOV-first architecture / catalogue implementation, real audit pending |
| 5 | Presentation | 20 | Clarity, structure, storytelling, broad reach | Before/during/after comparison, clear legends, plain-language metric definitions, uncertainty and caveats, short local case-study story, accessible map and downloadable report | UX and case-study deliverables / pending |
| 6 | Teamwork | 1–5 | Genuine collaboration | Named task ownership, contributions in PRs/issues, review activity, team process log and acknowledgement of science/data/UI roles | Team evidence / team-maintained |
| 7 | User experience | 1–5 | 5 = anyone can use it; 1 = significant training | Guided AOI/date selection, clear data-availability feedback, progress/error states, glossary, accessible map controls and explainable outputs | Frontend implementation / pending |
| 8 | NASA data usage | 1–5 | 5 = NASA open data plus other agency/third-party sources clearly shown | NISAR GCOV source granules visibly cited; ASF DAAC provenance; supporting Sentinel-2 and Bangladesh FFWC provenance; source credits in map legend and report | Source/data contract / partial |
| 9 | Challenge category identified | 0–1 | A 2026 challenge category is named | Project page and README explicitly say “Earth Science — Earth's surface” and “Dancing with the SARs” | Documentation / complete in repo docs |
| 10 | Repository access | 0–1 | GitHub or Drive link works and is open to all | Public GitHub repository; all required project files and no private-only dependencies for core demonstration | Repository setting / team must verify |
| 11 | Project page complete | 0–1 | NASA project page is filled in and submitted | Final challenge page with project summary, demo link, repository, team, media, data sources and submission status | Manual team action / pending |
| — | Women participation bonus | +5% | At least one woman member is on the team | Team membership and participation should be truthful and verifiable; bonus is not a software feature | Team eligibility / team must verify |

## Non-negotiable scientific acceptance gates

A public result must not be presented as a validated observation unless all applicable gates pass:

1. **Source gate:** actual NISAR GCOV granule names, acquisition time, data maturity and processing baseline retained.
2. **Product gate:** requested diagonal covariance layer exists; units and grid metadata are understood.
3. **Grid gate:** all scenes in a pixel-wise comparison have been aligned to one documented grid.
4. **Validity gate:** no-data, invalid looks and quality exclusions are masked, never silently treated as dry land.
5. **Baseline gate:** event inundation uses a documented pre-event water baseline.
6. **Persistence gate:** morphology candidates use multiple post-recession dates under comparable hydrological conditions.
7. **Reference gate:** independent reference labels exist and their source/date/scale are recorded.
8. **Validation gate:** confusion matrix, precision, recall, F1, IoU, sample count and sensitivity analysis are reported.
9. **Causality gate:** observed temporal association is not described as proof that the flood caused the erosion.
10. **Communication gate:** all non-validated or candidate outputs are visually labelled.

## Judge-friendly evidence checklist

- [ ] Challenge name and category shown in README and project page.
- [ ] NISAR is named as the primary data source, not hidden behind supporting imagery.
- [ ] Real source granules and timestamps shown in the demo.
- [ ] Data-maturity / processing-baseline policy explained.
- [ ] Method README immediately adjacent to every scientific module.
- [ ] Each scientific method states equations, assumptions, inputs, outputs, limitations and validation.
- [ ] Unit tests pass in CI.
- [ ] Real-scene validation report included; synthetic test results are not substituted.
- [ ] Map legends differentiate event water, baseline water, erosion candidates and deposition candidates.
- [ ] User can understand the main metrics without remote-sensing training.
- [ ] Open public repository and a working demo link verified.
- [ ] NASA project page completed and submitted by a team member.
- [ ] Team contributions are evident and genuine.
- [ ] Women participation bonus eligibility is checked truthfully.

## Evidence packaging convention

Every analysis run should eventually export:
- `source_manifest.json`
- `processing_parameters.json`
- `metrics.json`
- `validation_report.json`
- geospatial outputs with CRS, resolution and no-data metadata
- a short human-readable run summary.

The judge-facing project narrative should link to those artifacts instead of asking judges to infer science from screenshots alone.
