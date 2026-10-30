# RiverShift — NISAR-first river-change engine

RiverShift is a new, independent scientific engine within SARGuardian Dynamic for NASA Space Apps 2026 challenge **Dancing with the SARs**.

The canonical implementation is under:
- `Backend/science_adapter/river_shift/` — deployable science package.
- `Backend/app/river_shift.py` — authenticated, metadata-only GCOV catalogue API.
- `Backend/tests/river_shift/` — scientific unit tests.
- `tools/river_shift/` — command-line scientific scripts and their task READMEs.
- `Frontend/river-shift/` — first-stage user workspace.

Start with [the complete RiverShift README](../Backend/science_adapter/river_shift/README.md), then read:
- [Architecture](../docs/RIVERSHIFT_ARCHITECTURE.md)
- [Data contract](../docs/RIVERSHIFT_DATA_CONTRACT.md)
- [NASA judging-score acceptance plan](../docs/RIVERSHIFT_SCORECARD_ACCEPTANCE.md)
- [Implementation checklist](../docs/RIVERSHIFT_IMPLEMENTATION_CHECKLIST.md)

**Important:** This file is a navigation index only. Do not maintain a second copy of the scientific source code here. The Backend package is the sole source of truth.
