# Phase 02: integration candidate

The production contract remains schema **1.0.0**, model
**lastlight-dispatch-1.0.0** on `feature/physics-api`, [Draft PR #6](https://github.com/pablo228sos/lastlight/pull/6).
Equations, result shape and all generated fixtures are unchanged in this phase.
Abai owns frontend integration; Askar owns ML / Failure Frontier.

## Compatibility with PR #7

Reviewed final #6 physics at `874840dfede83a07699e792af6ff38f3995c348f`, then
the Phase 02 candidate `bd37f17ab4c704c1286025e885e21e962d0a0aa5`, against #7
first at `198eee9784c9a0e7990f1664d0498fa7390fef40` and again at its updated
head `0fff6f18d170c4b28e9d103576953039baae6dcd`. Their common ancestor remains
`776caa4d6922417731b7ff66bdbd553952aaeb32`; #7 includes the first #6 increment,
not the final `874840d` hardening. The updated #7 now includes ML/frontier code,
forecast/intelligence endpoints, frontend integration and additional CI steps.
Its dispatch engine is byte-identical to the earlier reviewed #7 engine
(Git blob `6681d01b642a092890c9c3a842783b732c4e7dc5`); the horizon defect remains.

| Change in #7 | Integration decision |
| --- | --- |
| Critical/noncritical demand arrays, exact length validation, per-interval dispatch demand, demand integrals | Useful; propose a dedicated reviewed Physics follow-up on final #6 |
| Disable scalar analytic autonomy when demand arrays are supplied | Retain with that extension; trace remains the source of observed failure |
| `physics_version` and ML version metadata | Distinguishing versions is useful in ML envelopes; retain physical `model_version` semantics in `SimulationResult` and put ML version in a separate estimate/envelope |
| Output `assumptions` list | Optional metadata proposal; current detailed MODEL.md is authoritative |
| Schema/model 1.1.0 and regenerated JSON | Unapproved until consumers review; do not mix with v1 fixtures/types |
| Shorter MODEL.md | Preserve #6's detailed topology, equations, validity limits and numerical guards |
| Stable HTTP error descriptions, structural JSON fixture comparison | Useful portability proposals; review separately without weakening fixture values or physical guards |
| Lazy-loaded ML/intelligence endpoints | API imports still work in the official lightweight environment; review routes/envelopes separately from dispatch and preserve the core service's independence |

A dry three-way merge of final #6 with updated #7 has textual conflicts in
`services/simulation/engine.py`, `services/simulation/api.py`,
`docs/physics/CONTRACT.md` and `docs/physics/MODEL.md`. Generated schemas/fixtures also differ and must be
regenerated from the chosen schemas/engine, not combined manually. The standalone
#7 checkout lacks #6's final exact-horizon correction, lower efficiency/capacity
bounds, hardened exception handling, extended tests, TypeScript proposal and
locked/offline tooling. These files are absent because #7 predates them, not
because Askar deliberately deleted them. A normal merge preserves files added
only in #6; replacing #6 wholesale with #7 would lose them.

Confirmed numerical defect: for `duration_hours=9.12`, PR #7 reports a critical
failure at the exclusive horizon with 1- and 15-minute steps, creating final
intervals of approximately 1.97e-13 and 5.33e-15 hours. This was reproduced at
both reviewed #7 heads. The original 21 physics tests pass but do not cover
this case. Official #6 returns null at all three 1/15/60-minute
steps, as required. Exact results: [pr7-horizon.json](evidence/phase02/pr7-horizon.json).
The case can be reproduced in either checkout with:

```python
from services.simulation.engine import simulate
from services.simulation.schemas import SimulationRequest
result = simulate(SimulationRequest(duration_hours=9.12, step_minutes=15))
print(result.summary.first_failure_utc)  # Official v1: None
```

The updated ML prediction response inherits `SimulationResult` but replaces its
`model_version` with the ML version, or null when ML is unavailable, while
`physics_version` identifies dispatch. Keep those meanings explicit in a
separate ML envelope rather than changing the meaning of the official result.
PR #7's frontend accepts any `schema_version` starting with `1.` but reads the
1.1-only `physics_version` field. That is not a valid v1 compatibility check:
Abai must adapt to the exact agreed schema and read `model_version` for v1.

Proposed ordering: review/validate #6, then port the useful demand extension onto
that final implementation with profile conservation, shedding, partial-horizon,
event timing and reproducibility tests. ML consumes an adapter to this engine.
No branch was overwritten, force-pushed or merged. The proposal was sent to
[Askar in PR #7](https://github.com/pablo228sos/lastlight/pull/7#issuecomment-6382698914).
**Agreement is pending**; a posted proposal is not teammate approval.

## Production CI activation and Windows evidence

Current active workflow on #6 is `Verify`. Its green
[run 40084249280](https://github.com/pablo228sos/lastlight/actions/runs/40084249280)
contains `web` and `reference-physics` jobs only. It does not execute the
production service suite. **There is no executed official production Python CI
run for #6 yet.** Updated #7 independently modifies Verify: its
[run 40084045257](https://github.com/pablo228sos/lastlight/actions/runs/40084045257)
passed 31 tests plus its schema checks on Ubuntu, but failed one browser smoke
test (five passed). That is evidence for #7's own subset, not the official
124-test suite, locked launcher, or Windows. It does not execute the official
`python -m services.simulation.check` command.

The exact reviewed change is [simulation-workflow.patch](simulation-workflow.patch)
and its source is [simulation-ci.yml](simulation-ci.yml). It adds a separate
`.github/workflows/simulation.yml` without altering existing Verify. Matrix:
Ubuntu + Windows, Python 3.12, hash-locked installs, official
`python -m services.simulation.check`, fresh launcher installation, live HTTP
fixture comparison/CORS/errors, offline stop/restart, fresh offline wheel setup,
and retained log/report artifacts. The Windows probe runs the actual `start.cmd`.

Activation is outside Issue #2's owned paths and was requested from
[Abai in Issue #1](https://github.com/pablo228sos/lastlight/issues/1#issuecomment-6382701940).
The shared workflow has not been changed. Once Abai agrees, the workflow owner
can apply this exact patch in a reviewable activation PR:

```sh
git apply --check docs/physics/simulation-workflow.patch
git apply docs/physics/simulation-workflow.patch
```

The candidate cannot be called **production-CI-verified** until both matrix jobs
actually pass. Native Windows is unavailable in this Linux environment;
Windows installation, console signal handling, HTTP and offline restart are
**unverified** until that runner executes. Linux evidence must not be cited as
Windows verification. The cross-platform probe is reproducible by anyone using
the commands in [README.md](README.md#reproduce-the-release-integration-check).

## Contract and frontend handoff

- [CONTRACT.md](CONTRACT.md): units, intervals, status/failure/censoring, versions,
  reproducibility, error envelopes, CORS and variable-load upgrade policy.
- [simulation-request.schema.json](simulation-request.schema.json) /
  [simulation-result.schema.json](simulation-result.schema.json): authoritative schemas.
- [fixtures/baseline.request.json](fixtures/baseline.request.json) /
  [fixtures/baseline.result.json](fixtures/baseline.result.json): full baseline.
- [fixtures/comparison.request.json](fixtures/comparison.request.json) /
  [fixtures/comparison.result.json](fixtures/comparison.result.json): 12-hour comparison.
- [fixtures/regression-16h.json](fixtures/regression-16h.json): observed 9.12 / 13.68 /
  12.16 h events; the 12-hour upgrade results correctly have null observed failure.
- [contracts.proposed.ts](contracts.proposed.ts), [FRONTEND.md](FRONTEND.md): reviewed
  type proposal, launch/request commands, playback and labelled offline replay.

Frontend adapter application and scene integration belong in Abai's PR; they
are not claimed complete here. Numerical verification and release logs are
recorded in [VALIDATION.md](VALIDATION.md).

Remaining demonstration blockers: activate and pass the production matrix,
including actual Windows evidence; obtain the required teammate review before
integration; keep Abai's adapter on the agreed v1 contract while the demand
extension remains under review. The synthetic model still excludes transient AC
network behaviour, startup/protection dynamics and measured school validation.
