# River morphology science module

This module identifies multi-date **persistent land/water transition candidates**. Its purpose is to prevent temporary flood-stage expansion from being confused with lasting channel migration.

See [persistent change task README](persistent_change/README.md) before inspecting the implementation.

## Required observation design

- Pre-event reference under a documented hydrological condition.
- At least two post-recession observations for the initial persistence test.
- Comparable NISAR product maturity, frequency, polarization, track/frame and grid.
- Common validity masks; invalid pixels must not be treated as dry land.
- Optional supporting Sentinel-2 interpretation and local water-level observations.

## Current scope

The initial algorithm reports erosion and deposition *candidates* from persistent water/dry fractions. It does not yet extract bankline vectors, build transects, estimate migration rates or attribute a change to a specific flood. Those tasks require dedicated geometry algorithms and separate validation READMEs.
