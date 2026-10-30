# RiverShift research decisions and scientific safeguards

## Challenge alignment
Target challenge: 2026 NASA Space Apps Challenge, “Dancing with the SARs”.
Primary sensor/product: NASA-ISRO NISAR L-band SAR, Level-2 GCOV.
Supporting sources may include Sentinel-2 surface reflectance, Bangladesh FFWC water-level data, and land-cover datasets. Supporting sources do not replace NISAR as the primary analysed radar input.

## Why GCOV
The official NISAR GCOV guide describes radiometrically and terrain-corrected gamma0 power values. Its diagonal covariance terms are real-valued and can be used like normalized/terrain-corrected SAR backscatter products. The available frequency/polarization terms depend on the acquisition mode.

GUNW and GOFF are not interchangeable with GCOV:
- GUNW is for unwrapped interferometric displacement.
- GOFF is for pixel offsets.
- GCOV is the appropriate branch for calibrated backscatter intensity screening.

## Input unit
GCOV diagonal covariance layers are gamma0 power, a linear quantity. Conversion to decibels is:
    gamma0_dB = 10 * log10(gamma0_power)

Do not use 20*log10 for power. Do not convert a layer already expressed in dB a second time. This implementation expects the caller to declare the input unit.

## Comparison gate
A valid pixel-wise time-series comparison needs:
- Same mission/instrument/frequency.
- Same diagonal covariance term.
- Same product maturity.
- Compatible acquisition geometry, orbit direction, relative orbit and frame.
- Same CRS, dimensions and affine transform after documented reprojection/resampling.
- Appropriate temporal separation and comparable hydrological stage.
A matching CRS/grid does not by itself prove comparable radar viewing geometry.

## Water screening
The initial algorithm is an interpretable open-water candidate screen using a common backscatter threshold. Otsu is offered only as exploratory global threshold estimation; it is not automatically optimal for all water/non-water classes or all river stages. Thresholds require AOI-specific reference validation.

Open water often produces low backscatter. Flooded vegetation may create double-bounce scattering and bright returns. Smooth soil, shadow and other dark targets may become false positives. Use context, ancillary optical imagery and independent reference validation.

## Flood semantics
newly_water_covered_area_km2 is the area classified as water during the event but not in the pre-event mask. It is not a measured flood depth, damage estimate, or proven floodplain inundation area. Permanent-water exclusion requires an aligned and documented permanent-water reference mask.

## Morphology semantics
Erosion candidates: pre-event land that is water in both post-recession observations.
Deposition candidates: pre-event water that is land in both post-recession observations.
Two post-event dates improve persistence screening but do not establish causality or permanence in a geomorphic/legal sense.

The symmetric boundary-distance statistic is a proximity-based change proxy. It does not identify signed retreat/accretion direction and is not a transect-derived migration rate. A later research milestone should implement centerline/active-belt extraction and signed perpendicular transects, then validate them against independently digitized banklines.

## Data maturity
Never mix BETA and PROVISIONAL products in the same analysis series. Store maturity with each output. Unknown maturity is not silently converted to a known maturity. Reprocessing/version changes require an explicit new series and a note in the provenance.

## Area calculations
Pixel areas are calculated from the affine transform determinant after requiring a projected CRS whose linear units are metres. Geographic-degree rasters must be reprojected before area summation. The script does not use a constant square-metre pixel area for geographic CRS.

## Validation
Synthetic tests check software contracts only. A real validation report needs an independent reference mask, date, method, confusion matrix, accuracy, precision, recall, F1, IoU, and area bias. Sentinel-2 can be a reference source when cloud/shadow masking and date proximity are documented, but it is not automatically ground truth.

## Open science references
- NISAR GCOV: https://nisar-docs.asf.alaska.edu/gcov/
- NISAR products and maturity: https://nisar-docs.asf.alaska.edu/products-overview/
- NISAR availability: https://nisar-docs.asf.alaska.edu/availability-overview/
- ASF search keywords: https://docs.asf.alaska.edu/api/keywords/
- ASF search manual: https://docs.asf.alaska.edu/asf_search/searching/
- NISAR HDF5: https://nisar-docs.asf.alaska.edu/data-format/
- GDAL NISAR guide: https://nisar-docs.asf.alaska.edu/using-nisar-data/using-gdal/
