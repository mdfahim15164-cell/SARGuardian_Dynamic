# Persistent river-change candidates

## Scientific task

Identify locations where land/water state appears to have changed persistently after an event. This produces **erosion candidates** and **deposition candidates**, not final geomorphological truth.

## Inputs

- Pre-event water mask.
- A stack of post-event water masks acquired after floodwater recedes.
- Validity masks for all observations.
- Persistence fraction (default 0.8).
- Minimum number of valid post-event observations (default 2).
- Pixel area in square metres.

All masks must be on the same grid and comparable acquisition geometry. The post-event observations should represent similar or documented hydrological conditions. Do not compare peak-flood water with a dry-season image and call every difference morphology.

## Definitions

- Persistent post-event water fraction >= threshold, where pre-event state was land: **erosion candidate**.
- Persistent post-event dry fraction >= threshold, where pre-event state was water: **deposition candidate**.

The implementation excludes cells that do not meet the required valid observation count. It reports post-event persistence fractions to retain evidence for each candidate.

## Outputs

- Erosion candidate mask and area (ha).
- Deposition candidate mask and area (ha).
- Net candidate land gain (ha).
- Per-pixel post-event water fraction and valid observation count.

## Limitations

- Land-to-water can reflect a changed water stage, reservoir operation or classification error.
- Water-to-land can reflect seasonal low water, exposed sediment or vegetation; it is not automatically stable new land.
- A candidate must be inspected in later observations and supported by optical/ancillary evidence before being labelled persistent erosion/accretion.
- No causal attribution to a specific flood event is made.

## Validation

Unit tests use multiple synthetic post-event masks to check that persistence threshold and minimum observation count are respected. Real-scene validation must compare polygons/banklines against independently interpreted imagery or field/reference data.
