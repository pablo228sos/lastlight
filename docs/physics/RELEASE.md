# LASTLIGHT: final physics handoff

**Status: official backend tested on Linux; production CI / Windows acceptance
is blocked pending Abai's workflow activation.** No physics, frontend or ML
source was changed for this final review. Neither PR was merged.

## Official source and contract

- Branch: `feature/physics-api`, [Draft PR #6](https://github.com/pablo228sos/lastlight/pull/6).
  Verified runtime source: `59b286b2d1a56a3b4634971e988e65a1eaaf0b2e`;
  subsequent final-handoff changes contain only documentation/evidence.
- Base URL: **http://127.0.0.1:8000**. Schema **1.0.0**;
  physics model **lastlight-dispatch-1.0.0**; HTTP namespace **/api/v1**.
- Authoritative contract: [CONTRACT.md](CONTRACT.md),
  [simulation-request.schema.json](simulation-request.schema.json),
  [simulation-result.schema.json](simulation-result.schema.json).
- Exact baseline pair: `docs/physics/fixtures/baseline.request.json` and
  `docs/physics/fixtures/baseline.result.json`. Comparison pair:
  `docs/physics/fixtures/comparison.request.json` and
  `docs/physics/fixtures/comparison.result.json`.
  `docs/physics/fixtures/regression-16h.json` observes all three failures.
- Frontend types/instructions: [contracts.proposed.ts](contracts.proposed.ts),
  [FRONTEND.md](FRONTEND.md). SOC is a fraction; power is AC kW; storage is DC kWh.
  Each trace row is `[t_utc, t_end_utc)` with start/end SOC and actual duration.

## Presentation scenario and commands

From repository root on Windows, Python 3.12 with its `py` launcher installed:

```powershell
.\services\simulation\start.cmd
```

In a second PowerShell terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
$run = Invoke-RestMethod http://127.0.0.1:8000/api/v1/simulations -Method Post -ContentType application/json -Body '{}'
$run.summary
$comparison = Invoke-RestMethod http://127.0.0.1:8000/api/v1/comparisons -Method Post -ContentType application/json -Body '{"baseline":{"duration_hours":12},"upgrade":"battery_36_kwh"}'
$comparison.upgraded.summary
```

After the first installation, Ctrl+C, then restart with
`.\services\simulation\start.cmd --offline`. **These are the intended Windows
entrypoints, not verified Windows executions.** The cross-platform entrypoint
is `python3.12 services/simulation/run.py`, executed on Linux; native macOS
has not been tested. API/CLI work offline after installation; first offline setup needs
same-platform wheels. Swagger UI uses CDN assets; `/openapi.json` remains local.

The baseline is synthetic: 24 kWh, SOC .8, reserve .2, discharge efficiency .95,
1.5 kW critical demand, zero solar, no grid, deliberate noncritical shedding.
It first fails at **9.12 h / 2026-01-01T09:07:12Z**. At 12 hours the 36 kWh
upgrade has **null observed failure**, ending SOC **.2736842105263151** (~27.4%).
13.68 h is its analytic reference, not a failure observed within that window.
For observed upgrade failure use `baseline.duration_hours=16`; full precharge
is the other approved comparison and fails at 12.16 h in that longer window.

## Verification and actual CI

Fresh final checks on Linux / Python 3.12.14: **124 passed, 0 failed; 99.44%**
engine/schema/API coverage; all 12 frozen schema/fixture files verified.
**20 launcher/HTTP checks** passed, including fresh hash-locked installation,
full response equality, CORS/errors, offline restart, graceful shutdown and
first-time offline wheel setup. The runtime source hashes remain unchanged.
See [final review evidence](evidence/final/review.json),
[official test log](evidence/final/official-check.linux.log), and
[offline restart log](evidence/final/offline-restart.linux.log).

- Official #6 [Verify 40084865359](https://github.com/pablo228sos/lastlight/actions/runs/40084865359)
  passed web + archived reference physics. It does **not** run the official 124-test suite.
- Askar #7 [Verify 40084814511](https://github.com/pablo228sos/lastlight/actions/runs/40084814511)
  passed its 31 Python tests and 6 browser tests, with 1 intentional media skip,
  on Ubuntu. The earlier browser failure is resolved. It is not official Windows
  or production-matrix evidence.
- **No approved production Python CI or Windows run exists yet.** Abai was asked
  to activate [simulation-workflow.patch](simulation-workflow.patch) in a reviewed
  integration branch: [coordination request](https://github.com/pablo228sos/lastlight/issues/1#issuecomment-6383191192).
  The unchanged [workflow source](simulation-ci.yml) runs the official check,
  real launcher/HTTP probe and offline restart on Ubuntu + Windows / Python 3.12.
  Shared workflow paths remain untouched; no teammate response/activation was observed.

## PR #7 at 7147b3f: verified improvements and remaining conflicts

Reviewed `7147b3f1d0808886c1ca7dc5954ba94edc1564bd`, not just the earlier revision.
Its engine is still blob `6681d01b642a092890c9c3a842783b732c4e7dc5`, unchanged
from `0fff6f1`; its common ancestor with #6 remains `776caa4`.

| Check | Verified result |
| --- | --- |
| Constant-input autonomy at steps 1/15/60 minutes | All 9 cases reproduce 9.12 / 13.68 / 12.16 h |
| Variable critical/noncritical loads | 100 seeded changing PV/grid/load scenarios pass independent AC/storage/system equations, equipment/SOC bounds and exact replay; maximum checked residual 6.86e-15 kWh |
| Partial profile interval | 1.1 h scenario integrates 3.0 kWh critical and 1.35 kWh noncritical demand correctly |
| 12-hour 36 kWh comparison | Correct null observed failure |
| Exclusive 9.12-hour horizon | Still wrong at 1- and 15-minute steps: false failure in a ~1.97e-13 / 5.33e-15 h final row; 60-minute step passes. Official #6 passes all three |
| Schema compatibility | #7 returns 1.1.0; official strict v1 rejects its extra metadata and resolved load-profile fields |
| Physics/ML identity | Plain simulation names physics correctly. Prediction inherits the result but changes `model_version` to ML/null; `physics_version` remains physical. Use an explicitly reviewed ML envelope/adapter |

Reproduce the remaining timing defect in a #7 checkout:

```python
from services.simulation.engine import simulate
from services.simulation.schemas import SimulationRequest
r = simulate(SimulationRequest(duration_hours=9.12, step_minutes=15))
print(r.summary.first_failure_utc)  # expected None; #7 gives 2026-01-01T09:07:12Z
```

A fresh dry merge still conflicts in `services/simulation/engine.py`,
`services/simulation/api.py`, `docs/physics/CONTRACT.md`, `docs/physics/MODEL.md`.
Useful demand/portability changes should be ported through a reviewed follow-up
on the official engine; team agreement is still pending. Preserve #6's complete
`tests/simulation/`, especially exact-horizon, energy, API, CLI and independent
legacy regressions, plus hash locks, check command and offline launcher. Their
absence on #7 comes from older ancestry, not intentional deletion by Askar.

## Frontend physics acceptance: reproduction for Abai

Abai's published #8 head is still `18f84dd`, with visual work only. The available
numerical frontend reviewed here is #7 at `7147b3f`. No frontend edits were made.
Verification used actual TypeScript modules rendered with React on the server,
the real adapter, source inspection and the linked browser CI. Local Chromium
is unavailable; this is not a local browser/GPU acceptance claim.

| Reproduction | Finding / acceptance requirement |
| --- | --- |
| Select school, disconnect, then FIRST FAILURE | Correct baseline: SOC 80.0% then 20.0%, failure 9.12 h; adapter keeps critical light on before failure and off after, with noncritical lights shed |
| Run official #6 API with #7 frontend; open MODEL & PROVENANCE | Validator accepts v1 but panel reads 1.1-only `physics_version`, so the physics version is blank. The validator even accepts `1.999.0`. Gate explicit supported versions and use v1 `model_version`; ML/frontier routes need a separate agreed adapter |
| Drag OUTAGE TRACE across baseline rows 36/37/38 | Row indices have equal slider spacing despite event-split durations; panel reads neither `t_end_utc` nor duration. Implement time-aware intervals/end labels; the existing FIRST FAILURE jump itself selects the correct event |
| Render `PhysicsPanel` with `comparison.result.json.upgraded`, index 47 | Correct NOT OBSERVED, but selected state is 11:45 / 28.5%, not horizon 12:00 / 27.4%. Add an explicit horizon end state using returned end SOC; never relabel last-row start as final SOC |
| Open school controls and inspect simulation requests | Only a fixed 16-hour baseline is requested; no comparison/36 kWh control exists. Connect the approved comparison endpoint for before/after demonstration |
| Inspect initial baseline row (`status=degraded`) | Critical-served text and lighting are correct, but no explicit degraded label is shown. Surface noncritical shedding separately from critical failure |
| Stop/block API, then disconnect | Explicit labelled rehearsal and no numeric result: correct. Approved fixture replay is not implemented; add an explicit synthetic fixture mode rather than silent success fallback |

## Remaining release gates and tested limits

Abai must activate/pass the official production matrix, including actual
Windows startup/HTTP/offline evidence, and confirm the integration target.
Abai's adapter must use the agreed contract and expose the approved upgrade and
fixture fallback; Askar's useful changes need reviewed reconciliation. Required
team review remains before merging either PR. These gates are not declared done.

This is a synthetic single-bus energy model with constant efficiencies, not a
measured school dataset or a transient voltage/protection/startup model. No
weather is inferred from missing solar inputs. Bounds/units are fixed by the
schemas; offline docs UI, native Windows/macOS and presentation-machine GPU
behaviour have the explicit limitations above. Full setup details remain in
[README.md](README.md), equations in [MODEL.md](MODEL.md).
