# Frontend physics integration

The school outage in the cinematic web app consumes the deterministic Physics API v1 contract from `feature/physics-api` commit `874840dfede83a07699e792af6ff38f3995c348f`. The authoritative sources are `services/simulation/schemas.py`, `docs/physics/simulation-result.schema.json`, and `docs/physics/CONTRACT.md` on that branch. PR #6 remains under team review; this frontend branch does not merge or modify it.

## Run the demonstration

From the frontend checkout, run `npm install` and `npm run dev`. The default school DISCONNECT GRID action requests a fresh run from `POST /api/v1/simulations`. The development server proxies `/api/v1` to `http://127.0.0.1:8000`. Start the physics service from an isolated checkout of `feature/physics-api` with `python services/simulation/run.py`. On Windows, `services\simulation\start.cmd` is also available. Confirm `http://127.0.0.1:8000/health` before presenting live mode.

The base URL can be set with `VITE_PHYSICS_API_URL` at build time. A deployed frontend needs a reachable Physics API and a compatible cross-origin or reverse-proxy configuration. The current development proxy is local only.

For a network-independent presentation, open the app with `?demo=offline`, then select the school and disconnect the grid. Alternatively, if a live request fails, the UI offers **USE VERIFIED REPLAY**. No failed request silently switches to replay.

## Numerical provenance

The two files under `apps/web/src/data/` are byte-for-byte copies of the backend-generated fixtures in `docs/physics/fixtures/` at the commit above. They are validated with the same frontend response checks as live JSON.

| File | SHA-256 | Meaning |
| --- | --- | --- |
| `baseline.result.json` | `EE0882B680A3B31D794506493ECEAD7BD3337C19582ED9AF26CCDB8940B06C40` | 24 kWh baseline, observed critical failure at 9.12 h |
| `comparison.result.json` | `035551759D8C378969F4513652A1097F1FE7F26C85FAC7E70451A98BF38E34A3` | 24 to 36 kWh comparison, no observed upgrade failure in 12 h |

Both carry model version `lastlight-dispatch-1.0.0` and synthetic input provenance. The 13.68 h upgraded autonomy is an analytical battery-only reference from the engine. It is not an observed failure inside the 12-hour trace.

`apps/web/src/lib/contracts.ts` retains the backend's snake_case result fields. `physics.ts` validates identities, continuity of real interval boundaries, SOC bounds, energy residuals, trace coverage, and agreement of the first critical failure with the summary. `usePhysicsRun.ts` is the sole adapter from numerical trace to scene lighting. Playback speed changes presentation time only. The school and camera geometry do not change with the physics run.

The initial grid-connected view is a presentation state before the modeled outage. The default trace starts at outage time zero with the grid offline. Rooftop PV is visible as an illustrative physical asset, while the approved scenario supplies zero PV power. District geometry, facility labels and equipment placement are illustrative. No measured school telemetry, mapped utility topology, weather feed or trained ML prediction is implied.

## Verification

Run `npm run build`, `npm run lint`, and `npm run test:smoke` from the frontend checkout. `apps/web/tests/physics.spec.ts` checks unequal trace intervals, the exact failure boundary, SOC and load display, scene response, right-censored comparison, API failure, reset, and two presentation viewports. With the isolated backend running, set `LASTLIGHT_LIVE_API=1` before `npm run test:smoke` to include a real HTTP simulation and comparison test.

The recorded browser walkthrough and 1440×900 / 1920×1080 screenshots are in `evidence/phase-03-physics/`. The separate Failure Frontier boundary remains pending until the ML team supplies a validated payload contract. No values are fabricated for it.
