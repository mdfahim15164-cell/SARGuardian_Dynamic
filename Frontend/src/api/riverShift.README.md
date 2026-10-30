# Frontend API task: RiverShift catalogue adapter

## Purpose

src/api/riverShift.ts is the browser-side client for the authenticated RiverShift catalogue endpoint.

## Flow

1. Require a signed-in Firebase user.
2. Obtain a Firebase ID token.
3. Send the AOI/date/maturity request to POST /api/river-shift/catalog/search.
4. Parse and type the real ASF metadata response.
5. Return catalogue metadata only; do not manufacture science results.

## Environment

The API base URL uses VITE_SARGUARDIAN_API_URL and defaults to http://localhost:8000 for local development. Only public browser configuration may use VITE_*. Do not place server-side keys or credentials in frontend variables.

## Response interpretation

The requested_maturity_filter is distinct from a scene's actual data_maturity. The latter can be null when ASF did not return that property. The UI must show this distinction.

## Failure handling

The client gives recoverable errors for missing authentication, failed token acquisition, network failure and non-2xx API responses.
