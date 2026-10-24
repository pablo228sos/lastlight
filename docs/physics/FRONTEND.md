# Frontend handoff for Abai

The Physics service is the numerical source for both frontend and Askar's ML
adapter. Base URL: **http://127.0.0.1:8000**. HTTP namespace: `/api/v1`.
Supported schema: **1.0.0**. Model: **lastlight-dispatch-1.0.0**.
Types for review: [contracts.proposed.ts](contracts.proposed.ts). The existing
frontend interfaces are preserved; this file supplies the interval and version
fields needed for integration. Apply those additions in your frontend PR.

## Start and verify on Windows

From the repository root, in the first PowerShell terminal:

```powershell
.\services\simulation\start.cmd
```

Python 3.12 and its `py` launcher must be installed. Leave that terminal open.
In a second PowerShell terminal, also at the repository root:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
$body = Get-Content .\docs\physics\fixtures\baseline.request.json -Raw
$run = Invoke-RestMethod http://127.0.0.1:8000/api/v1/simulations -Method Post -ContentType application/json -Body $body
$run.summary
$comparisonBody = Get-Content .\docs\physics\fixtures\comparison.request.json -Raw
$comparison = Invoke-RestMethod http://127.0.0.1:8000/api/v1/comparisons -Method Post -ContentType application/json -Body $comparisonBody
$comparison.upgraded.summary
```

Stop with Ctrl+C; restart without package-index access:

```powershell
.\services\simulation\start.cmd --offline
```

On macOS: `python3.12 services/simulation/run.py`, with the same local URLs.
This handoff does not claim native Windows verification; see [RELEASE.md](RELEASE.md).

## Requests

Minimum successful simulation request: `POST /api/v1/simulations`,
`Content-Type: application/json`, body `{}`. All defaults are deterministic.

Complete baseline request, exactly [baseline.request.json](fixtures/baseline.request.json):

```json
{
  "start_utc": "2026-01-01T00:00:00Z",
  "duration_hours": 12.0,
  "step_minutes": 15,
  "seed": 0,
  "battery": {
    "capacity_kwh": 24.0,
    "initial_soc": 0.8,
    "minimum_soc": 0.2,
    "maximum_soc": 1.0,
    "charge_efficiency": 0.95,
    "discharge_efficiency": 0.95,
    "max_charge_kw": 6.0,
    "max_discharge_kw": 8.0
  },
  "inverter": {
    "max_kw": 8.0,
    "islanding_capable": true
  },
  "load": {
    "critical_kw": 1.5,
    "noncritical_kw": 2.0,
    "shed_noncritical_during_outage": true
  },
  "solar": {
    "generation_kw": 0.0,
    "profile_kw": null,
    "islanding_capable": false
  },
  "grid": {
    "online": false,
    "profile_online": null,
    "import_limit_kw": 50.0,
    "charge_battery": false
  },
  "provenance": {
    "category": "synthetic",
    "references": [
      "docs/physics/MODEL.md"
    ]
  }
}
```

Comparison request, `POST /api/v1/comparisons`:

```json
{"baseline": {}, "upgrade": "battery_36_kwh"}
```

Use `"full_precharge"` for the other approved upgrade. To **observe** all three
failure events, pass `"baseline": {"duration_hours": 16}`. Do not submit load
profiles from PR #7 to v1; they are not part of this approved input contract.

## Response and browser adapter

The complete successful response is [baseline.result.json](fixtures/baseline.result.json).
This is a shortened excerpt of its real values, not a complete response or a
second fixture; the full file includes every energy field and all 49 intervals:

```json
{
  "run_id": "3055515b-6053-57cc-b40c-ec6302c24726",
  "model_version": "lastlight-dispatch-1.0.0",
  "schema_version": "1.0.0",
  "summary": {
    "critical_survival_hours": 9.12,
    "first_failure_utc": "2026-01-01T09:07:12Z",
    "survived_full_window": false,
    "ending_soc": 0.20000000000000004
  },
  "trace": [
    {
      "t_utc": "2026-01-01T00:00:00Z",
      "t_end_utc": "2026-01-01T00:15:00Z",
      "elapsed_hours": 0.0,
      "duration_hours": 0.25,
      "battery_soc": 0.8000000000000002,
      "battery_soc_end": 0.7835526315789475,
      "critical_served_kw": 1.5,
      "critical_demand_kw": 1.5,
      "status": "degraded"
    }
  ]
}
```

A minimal adapter belongs in the frontend owner's PR. Use the reviewed proposed
types; validate the schema version before playback, and handle HTTP errors
separately from a network/connection error:

```ts
import type { SimulationRequest, SimulationResult } from './contracts'

export async function fetchSimulation(input: SimulationRequest = {}): Promise<SimulationResult> {
  const response = await fetch('http://127.0.0.1:8000/api/v1/simulations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
    signal: AbortSignal.timeout(10_000),
  })
  const body = await response.json()
  if (!response.ok) throw new Error(body.error?.message ?? `HTTP ${response.status}`)
  if (body.schema_version !== '1.0.0') throw new Error('Unsupported physics schema')
  return body as SimulationResult
}
```

Allowed Vite origins are `http://localhost:5173`, `http://127.0.0.1:5173` and the
corresponding port **4173** preview origins. Configure a fixed Vite port: an
automatically selected 5174 is not allowed. Do not use `mode: 'no-cors'`, which
makes the response unreadable. HTTPS-hosted pages may be blocked from a local
HTTP API; the approved demonstration path is local Vite + local backend.

## One trace drives every displayed number

- Power fields are AC-side **kW**; battery energy fields are DC-side **kWh**.
- SOC is a fraction. Display `100 * row.battery_soc` as a percentage, rounded for
  readability. It is the state at the start of this interval. At the final
  horizon, display `run.summary.ending_soc` (equal to the final row's end SOC).
- For a playback time `h` in hours from the simulation start, select the row for
  which `row.elapsed_hours <= h < row.elapsed_hours + row.duration_hours`.
  Advance on its actual end, not on a fixed 15-minute timer or a row index.
  The baseline has a split at 09:07:12 UTC. A row's powers/status apply throughout
  its half-open interval; `battery_soc_end` is the state at its end.
- Use `row.status === 'critical_failure'` for a current critical-load failure.
  `degraded` means only noncritical demand is unmet; the baseline deliberately
  sheds 2 kW of noncritical load and is degraded even before its critical failure.
  `normal` means connected and fully served; `islanded` means disconnected and
  fully served. Grid state is independently available as `row.grid_online`.
- `summary.first_failure_utc` / `critical_survival_hours` record the **first**
  historical shortfall. They remain set even if the grid later returns. Check
  `!== null`, not truthiness: a power bottleneck can fail immediately at hour 0.
- A null first failure means none was observed inside the calculation window.
  At 12 hours the 36 kWh and full-precharge upgrades both have null observed
  failure. Display “no critical failure within 12 h”. Their analytic references
  of 13.68 / 12.16 h are separately labelled assumptions, not observed events.
  [regression-16h.json](fixtures/regression-16h.json) observes all three failures.
- Read totals from `summary`; take the live power/state indicators from the
  selected row of that same result. Keep `run_id` attached to playback; replacing
  a run must replace all its indicators together. Do not recompute battery drain,
  time to failure or upgrade effects in JavaScript.

## Connection errors and approved offline replay

For a rejected fetch/timeout, stop presenting changing runtime telemetry and
show that the local API is unavailable. HTTP 422 is a request error with the
structured envelope in [error.schema.json](error.schema.json), not a reason to
silently play a successful result. A 500 requires surfacing the service failure.

Offer an explicit “Replay approved synthetic fixture” mode. Bundle the exact
[baseline.result.json](fixtures/baseline.result.json) and/or
[comparison.result.json](fixtures/comparison.result.json) in the frontend PR and
load them as typed JSON. Feed their complete traces into the **same** playback
path as live results. Show both the fixture source and `provenance.category`;
these fixtures are synthetic, never measured school data. Label baseline and
upgraded run IDs separately. An offline fixture is immutable: changing equipment
controls requires a new API run, not editing its numbers in JavaScript.

`/docs` uses CDN assets and may be unavailable offline. HTTP endpoints,
`/openapi.json`, the offline CLI and approved JSON playback remain local.
