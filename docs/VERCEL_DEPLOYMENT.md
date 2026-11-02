# Vercel deployment setup

This repository is a monorepo with two separate Vercel projects. The Vercel account must be connected and each project must be linked to the GitHub repository before Vercel variables or deployments can be managed.

## Project settings

| Project | Root directory | Build/runtime | Production branch |
| --- | --- | --- | --- |
| `sarguardian-frontend` | `Frontend/` | Vite, `npm run build`, output `dist` | `main` |
| `sarguardian-backend` | `Backend/` | FastAPI Python runtime; `index.py` exports `app` | `main` |

The frontend SPA rewrite is already in `Frontend/vercel.json`. Vercel recognizes the FastAPI application exported by `Backend/index.py` when the project root is `Backend/`; no `uvicorn` server command should be configured for the Function deployment.

## Frontend environment variables

Set these on the **frontend project** before its next build. Values are browser-visible; never put server credentials in a `VITE_` variable.

| Variable | Type | Value |
| --- | --- | --- |
| `VITE_SARGUARDIAN_API_URL` | Plain | The final HTTPS backend project origin, with no trailing slash. |
| `VITE_GOOGLE_MAPS_API_KEY` | Plain/public browser key | A Google Maps JavaScript API key restricted to the deployed frontend origins. |
| `VITE_FIREBASE_API_KEY` | Plain/public Firebase web config | Existing Firebase web application configuration. |
| `VITE_FIREBASE_APP_ID` | Plain/public Firebase web config | Existing Firebase web application configuration. |
| `VITE_FIREBASE_AUTH_DOMAIN` | Plain/public Firebase web config | Existing Firebase web application configuration. |
| `VITE_FIREBASE_MEASUREMENT_ID` | Plain/public Firebase web config | Existing Firebase web application configuration; optional if unused. |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | Plain/public Firebase web config | Existing Firebase web application configuration. |
| `VITE_FIREBASE_PROJECT_ID` | Plain/public Firebase web config | Existing Firebase web application configuration. |
| `VITE_FIREBASE_STORAGE_BUCKET` | Plain/public Firebase web config | Existing Firebase web application configuration. |

`VITE_SARGUARDIAN_API_URL` cannot be finalized until the backend project has a deployed HTTPS origin. Changing any variable requires a new deployment because Vite embeds these values during the build.

## Backend environment variables

Set these on the **backend project only**. Choose Vercel's encrypted/sensitive type for every secret.

| Variable | Type | Value / requirement |
| --- | --- | --- |
| `APP_ENV` | Plain | `production`. |
| `CORS_ORIGINS` | Plain | Comma-separated exact production frontend origin(s), for example `https://<frontend-domain>`; do not use `*` with credentials. |
| `SUPABASE_URL` | Plain | The active production Supabase project HTTPS URL. |
| `SUPABASE_SERVICE_ROLE_KEY` | Sensitive | Server-only Supabase secret/service-role key. Never expose to frontend. |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Sensitive | Firebase Admin service-account JSON for authenticated API routes. |
| `ASF_CATALOG_ENABLED` | Plain | `true` for the public read-only ASF catalogue endpoint. |
| `ASF_SEARCH_URL` | Plain | `https://api.daac.asf.alaska.edu/services/search/param` (or retain the code default). |
| `ASF_MAX_RESULTS` | Plain | `2000` (or retain the code default). |
| `ASF_TIMEOUT_SECONDS` | Plain | `20` (or retain the code default). |
| `PREFLIGHT_TTL_SECONDS` | Plain | `86400` (or retain the code default). |

Production startup currently requires `APP_ENV=production`, non-empty `CORS_ORIGINS`, `SUPABASE_URL`, and `SUPABASE_SERVICE_ROLE_KEY`. Do not bypass this by deploying production with `APP_ENV=development` or placeholder secrets. If preserving the existing authenticated Landslide API, configure the already documented Drive and Firebase values too; do not turn on `DISPLACEMENT_ACTIONS_ENABLED` until its migrations, worker secrets, callback URL and GitHub workflow have been independently checked.

Never set `EARTHDATA_TOKEN` on the frontend. The current Vercel API only searches public catalogue metadata; it does not download or process NISAR imagery.

## GitHub Actions variables

With Vercel's GitHub integration, **no Vercel GitHub Action variables are needed**: Vercel creates previews for branch/PR changes and deploys the configured production branch. The existing RiverShift catalogue audit and science-test workflows do not require Vercel credentials.

If the team later chooses to deploy through a GitHub Actions workflow instead of Vercel's Git integration, configure:

| GitHub setting | Scope | Purpose |
| --- | --- | --- |
| `VERCEL_TOKEN` | Actions secret | Vercel deploy token with the least required project/team access. |
| `VERCEL_ORG_ID` | Actions variable | The owning Vercel team ID (`team_...`). |
| `VERCEL_FRONTEND_PROJECT_ID` | Actions variable | Frontend project's Vercel ID. |
| `VERCEL_BACKEND_PROJECT_ID` | Actions variable | Backend project's Vercel ID. |
| `VERCEL_CLI_VERSION` | Actions variable | Reviewed, exact Vercel CLI version. |

Those IDs do not exist in this checkout because the connected Vercel account currently has no visible team or projects. Do not invent them. The repository has no Vercel deployment workflow that reads these variables today.

## What Vercel does and does not run

Vercel can serve the frontend and the FastAPI metadata API. The NISAR processing commands remain local CLI tools and are not connected to a web job endpoint. NISAR GCOV products are multi-gigabyte files; Vercel Functions have a 4.5 MB request/response payload limit and finite invocation duration. A true web-triggered processing service needs a separately provisioned queue/worker, object storage, job/status API, authentication, Earthdata credentials in the worker only, retention policy and independent validation. Do not label catalogue search or an asynchronous audit as live image processing.

## Release sequence

1. Connect the intended Vercel account/team and create or select both projects with the roots above.
2. Enter the real production secret values directly in Vercel as sensitive variables. Never commit them or paste them into chat.
3. Deploy the backend and confirm its health and `/api/river-shift/catalog/search` behavior; obtain its final HTTPS origin.
4. Set `VITE_SARGUARDIAN_API_URL` and public browser config on the frontend, then deploy it.
5. Verify CORS, Google Maps AOI drawing, catalogue results and the existing Landslide route.
6. Only then merge the reviewed PR into `main` if the owner still intends to release it. A Vercel deployment does not make real GCOV processing or all-river coverage available.
