# Event inundation accounting

## Scientific task

Calculate the area that is water during a selected event but was not water in the pre-event baseline. The function is intentionally separate from water classification so the baseline/event classification choices remain inspectable.

## Definition

```
newly_inundated = event_water AND NOT baseline_water
```

The baseline and event masks must share the same grid, projection, dimensions and validity definition. The pixel area must be calculated from the source grid's projected coordinate spacing and CRS units, not assumed to be 10 m merely because a product is called NISAR.

## Outputs

- Baseline water area (km²).
- Event water area (km²).
- Newly inundated area (km²).
- Water-area percentage change relative to baseline (null if baseline area is zero).
- Newly inundated pixel mask and common valid-pixel count.

## Interpretation

This measures a water-extent difference, not water depth, flood volume, causal impact or permanent channel migration. Permanent-water exclusion depends on the baseline supplied. For a stronger baseline, use multiple pre-event observations and a persistent-water composite rather than a single acquisition.

## Validation

Unit tests use a small raster with a hand-calculated number of changed pixels and area. A real study must also document co-registration/grid equivalence, acquisition dates, reference water labels and threshold sensitivity.
