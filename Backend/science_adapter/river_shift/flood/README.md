# Flood science module

This module contains two distinct scientific tasks. Their outputs must remain separate in the UI and reports.

1. [Open-water candidate classification](water_classification/README.md) — classify low-backscatter candidates from one GCOV diagonal power layer.
2. [Event inundation accounting](inundation/README.md) — subtract a documented pre-event water baseline from event water.

The classification stage answers “where does this scene look like open water?” The inundation stage answers “which valid pixels changed from non-water in the baseline to water during the event?” A single scene cannot establish newly inundated area.

## Minimum event package

- One baseline observation or a multi-date baseline water composite.
- One event observation closest to the independently recorded event peak.
- A comparable grid, CRS, frequency, polarization term and processing maturity.
- Source metadata and threshold parameters.
- A reference label set for validation.

## Exclusions

This module does not calculate flood depth, discharge, water velocity, flood volume or a public warning. Flooded vegetation requires additional features and independent validation.
