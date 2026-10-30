# Sirajganj–Kazipur Jamuna AOI (candidate only)

## Status
**CANDIDATE_NOT_APPROVED.** This polygon is supplied only to run the first NISAR GCOV catalogue/footprint audit. It is not a final scientific study boundary, bankline, flood extent, administrative boundary or field-validated corridor.

## WGS84 coordinates
    POLYGON ((89.62 24.43, 89.78 24.43, 89.78 24.68, 89.62 24.68, 89.62 24.43))

Approximate area: 449.8 km² (spherical screening estimate). The audit script projects the polygon to the local UTM zone before calculating its area and footprint overlap.

## Why this candidate
The rectangular envelope is intended to include the Jamuna reach around Sirajganj Hard Point and Kazipur. Approximate reference locations used only to place the initial search window:
- Sirajganj Hard Point: approximately 24.47893° N, 89.71322° E.
- Sirajganj SW49 / Hard Point gauge: approximately 24.4685° N, 89.7196° E (secondary published station list; verify against the current BWDB/FFWC station registry).
- Kazipur SW49A: approximately 24.6698° N, 89.6491° E (secondary published station list; verify against the current BWDB/FFWC station registry).

The boundary is deliberately a broad rectangle because its first purpose is to determine whether NISAR GCOV frames intersect the target reach. It is not a substitute for a digitised river-corridor AOI. The final polygon should follow the intended active channel and adjacent floodplain and should be reviewed by the science team.

## Event window candidate
The first acquisition audit uses 2026-06-17 through 2026-10-31, PROVISIONAL maturity only. A September 2026 high-water episode is a candidate event for later matching, but do not call a date the flood peak until the original FFWC/BWDB Sirajganj and Kazipur gauge time series has been downloaded and reviewed.

The reported August 9 episode should not be treated as a verified danger-level flood: the cited report stated that Sirajganj and Kazipur gauges were still below their danger levels on that date even though low-lying areas were inundated. The event date, stage and peak should come from the station series, not a news headline.

## Required before scientific analysis
1. Confirm the final AOI and boundary with the team.
2. Query ASF DAAC for actual NISAR Level-2 GCOV products and save the catalogue manifest.
3. Run the footprint-coverage audit. Do not use products merely because their footprints intersect the AOI.
4. Find at least three dates that meet the same maturity, direction, relative orbit, bandwidth/mode and polarization constraints, with a documented AOI-coverage threshold.
5. Inspect the actual product footprints and acquisition geometry in GIS.
6. Retrieve official FFWC/BWDB station water-level history for the same dates and choose before/event/post dates.
7. Download exact selected granules, preserve their product IDs and SHA-256 receipts, then run the science scripts.

## Sources / reference links
- NISAR GCOV product naming, single-acquisition metadata and pixel-spacing guide: https://nisar-docs.asf.alaska.edu/gcov/
- NISAR product naming convention: https://nisar-docs.asf.alaska.edu/naming-conventions/
- ASF Search API and NISAR frameCoverage parameters: https://docs.asf.alaska.edu/api/keywords/
- NASA NISAR Provisional collection availability and maturity: https://nisar-docs.asf.alaska.edu/availability-overview/
- FFWC public portal and station information: https://ffwc.gov.bd/
- Sirajganj Hard Point place reference: https://mapcarta.com/34912738
- Daily Star report of the August 9 2026 Jamuna rise: https://www.thedailystar.net/news/bangladesh/news/jamuna-swells-sirajganj-low-lying-areas-inundated-4243436

The candidate coordinates and the area estimate are screening aids. They are not verified hydrological boundaries.
