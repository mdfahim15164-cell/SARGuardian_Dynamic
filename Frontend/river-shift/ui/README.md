# RiverShift workspace UI

## Purpose

This route is an authenticated first-stage workspace for the RiverShift engine. It gives the user a guided NISAR GCOV catalogue audit before scientific processing is enabled.

## Current user flow

1. Enter one WGS84 polygon in WKT.
2. Set an observation date window.
3. Choose a single NISAR data maturity (PROVISIONAL or BETA).
4. Request a metadata-only ASF search.
5. Inspect returned granule IDs, times, direction, path/frame, polarization and source-reported file size.

## Honest product state

The workspace does not pretend that catalogue discovery is a water map. It does not download files, classify water, calculate inundated area or measure erosion. Those capabilities are not connected yet. The interface makes this explicit in both result messaging and the page footer.

## UX criteria

- Clear task order and current phase.
- Simple form labels and validation.
- Loading, error, empty and populated result states.
- Source links and a maturity warning.
- Responsive table and no-data explanations.
- No fabricated metric cards.
