# API task: RiverShift GCOV catalogue search

## Endpoint

POST /api/river-shift/catalog/search

This endpoint requires the existing Firebase Bearer ID token. It does not create a durable job, download a product, or run scientific processing.

## Request

    {
      "coordinates": [[89.6,25.0],[89.8,25.0],[89.8,25.2],[89.6,25.2],[89.6,25.0]],
      "start_date": "2026-06-17",
      "end_date": "2026-07-20",
      "data_maturity": "PROVISIONAL",
      "max_results": 100
    }

Coordinates must be a closed WGS84 polygon in longitude/latitude order. AOI is limited to 1,000 km². Date order is validated and a request cannot exceed 366 days.

## Response contract

- Actual granule names and metadata returned by ASF.
- Requested maturity filter is returned separately from each product's reported maturity.
- Missing per-product maturity remains null; the query filter is not copied into the product metadata field.
- Response is explicitly labelled catalogue-only, data_downloaded=false and scientific_analysis_performed=false.
- Scene identity is parsed from the granule name only when it matches the documented convention.

## Security

- Firebase authentication is verified server-side.
- Earthdata, GitHub, Supabase, Firebase Admin and Google Drive secrets are not passed to the browser.
- AOI/date bounds are checked before ASF is called.

## Tests

Backend/tests/test_river_shift_api.py covers authentication, successful adapter response, invalid open polygon and reversed dates. Catalogue adapter tests cover query parameters and separation between product maturity and ASF query filter.

## Limitations

This endpoint is metadata discovery only. A catalogue result does not prove temporal comparability. The caller must run the scene identity and HDF5 grid gates before pixel-level analysis.
