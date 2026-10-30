# RiverShift workspace

## Current milestone

The first UI milestone is a guided NISAR GCOV data-availability audit. Users provide one WGS84 AOI polygon, a date window, an ASF maturity filter and a result limit.

## User workflow

1. Sign in using the existing Firebase flow.
2. Open the RiverShift engine from the SARGuardian home page or visit /river-shift.
3. Enter the study polygon as WKT.
4. Select observation dates and one maturity filter.
5. Search the live ASF NISAR GCOV catalogue.
6. Inspect returned granules, acquisition timestamps, orbit direction/track, frame, polarization, CRID and file size when the archive provides them.

## Scientific honesty

The page reports catalogue presence only. It does not download HDF5, classify water, calculate flooded area, detect erosion, estimate flood depth or issue warnings. No fictional KPI values are shown.

## Related documentation

- UI task README: ui/README.md
- Frontend API task README: ../src/api/riverShift.README.md
- Overall architecture: ../../docs/RIVERSHIFT_ARCHITECTURE.md
- Scorecard acceptance plan: ../../docs/RIVERSHIFT_SCORECARD_ACCEPTANCE.md
