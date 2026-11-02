# RiverShift live-processing setup

The RiverShift page accepts a user-drawn WGS84 AOI, a date range, one NISAR maturity, frequency and diagonal term, an event date, and a shared water threshold method. The backend refreshes the NASA CMR granule list and dispatches `.github/workflows/river-shift-gcov-process.yml`. The worker checks footprint coverage and acquisition compatibility before downloading exact products.

## Current service state

- The connected `SARGuardian_Dynamic` Supabase project is healthy. Its `river_shift_jobs` table and migration `20261102200956` are already present; this code does not need a new live schema change.
- The production frontend is available at `https://sarguardian-frontend.vercel.app/river-shift`; the Google Maps key and HTTPS backend API URL are configured. The frontend and backend deployments are READY on main commit `56816ac`.
- The production Vercel backend does not currently have the `RIVERSHIFT_*` dispatch settings. `RIVERSHIFT_ACTIONS_ENABLED` therefore defaults to `false`, so the live-processing button will report that dispatch is not configured.
- The processing workflow is now present on GitHub's default `main` branch. GitHub can dispatch it with the `main` ref once the backend settings and repository secrets below are configured.
- A real processing run has not completed. The code and workflow do not turn catalogue matches into fabricated results.

## GitHub repository secrets

Add these secrets to `mdfahim15164-cell/SARGuardian_Dynamic` before dispatch:

| Secret | Use |
| --- | --- |
| `RIVERSHIFT_CALLBACK_SECRET` | HMAC key used to authenticate worker status and result callbacks. Use the same value in Vercel. |
| `EARTHDATA_TOKEN` | Current Earthdata bearer token for exact ASF product downloads. |
| `GOOGLE_DRIVE_OAUTH_CLIENT_JSON` | Private Google Drive OAuth client JSON. |
| `GOOGLE_DRIVE_REFRESH_TOKEN` | Refresh token for the account that owns the private result folder. |
| `GOOGLE_DRIVE_FOLDER_ID` | Private parent folder for job result bundles. |

The worker checks Drive access and the private-folder setting before downloading satellite data. It never makes result files public and never stores raw NISAR HDF5 products in GitHub or Supabase.

## Vercel backend production variables

Set these on `sarguardian-backend`:

| Variable | Value or handling |
| --- | --- |
| `RIVERSHIFT_ACTIONS_ENABLED` | `true` after all GitHub secrets below are ready. |
| `RIVERSHIFT_GITHUB_ACTIONS_TOKEN` | Secret fine-grained GitHub token with Actions write access to this repository. |
| `RIVERSHIFT_GITHUB_ACTIONS_REPOSITORY` | `mdfahim15164-cell/SARGuardian_Dynamic` |
| `RIVERSHIFT_GITHUB_ACTIONS_WORKFLOW` | `river-shift-gcov-process.yml` |
| `RIVERSHIFT_GITHUB_ACTIONS_REF` | `main` after the workflow and worker are merged to the default branch. |
| `RIVERSHIFT_CALLBACK_SECRET` | The same secret as the GitHub repository secret above. |
| `RIVERSHIFT_PUBLIC_API_URL` | `https://sarguardian-backend.vercel.app` (API origin only; no `/api` suffix). |

After changing Vercel variables, redeploy the backend so the production runtime receives them. Keep all tokens and OAuth credentials out of `VITE_` variables, source files, workflow inputs and logs.

## Real-data limits

The processing request is geography-independent; it does not default to Bangladesh. NISAR must still have suitable observations for the chosen place and dates. The worker requires four comparable dates, at least 90% catalogue footprint coverage per selected date, and the same maturity, orbit/frame group, bandwidth/polarization mode and diagonal term. It processes up to twelve actual observed dates and twenty-four granules. The API currently caps the AOI at 1,000 km² and the selected date span at 366 days. Requests outside the mission coverage or those limits fail with an explanation.

The playback steps through actual acquisition dates and does not interpolate daily images. Erosion, deposition, open-water and flood-period layers remain provisional. The map uses simplified, small-patch-filtered GeoJSON previews for display; full-resolution outputs are retained in the private result bundle. Independent optical/reference validation and authoritative event-date evidence are still required before a verified release.
