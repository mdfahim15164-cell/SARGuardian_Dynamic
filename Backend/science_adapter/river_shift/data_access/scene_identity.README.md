# NISAR GCOV scene identity parser

## Purpose

Extract acquisition and processing identity from the NISAR GCOV granule name. ASF catalogue responses do not always expose every attribute as a separate searchable field, so the original granule name is retained as an auditable metadata source.

## Parsed fields

- Product processing type (PR / UR / OD).
- Mission cycle and relative orbit track.
- Ascending/descending direction.
- Frame number.
- Acquisition mode and polarization mode.
- Source mode.
- Radar start/end time (UTC).
- CRID (processing release identifier).
- Orbit accuracy and coverage.

The mission cycle is recorded but is intentionally not a hard compatibility key: repeat acquisitions in later cycles may observe the same ground track.

## Validation

A parser mismatch returns None. It must not guess fields or silently substitute request-form values for missing product identity. Actual per-product data maturity is taken from ASF metadata when supplied; otherwise the report distinguishes the requested ASF maturity filter from per-granule metadata.

## Why this matters

Different relative orbit, frame, direction, acquisition mode, polarization mode or CRID can introduce non-comparable geometry or processing. Such scenes must not be silently combined in a pixel-wise change stack.
