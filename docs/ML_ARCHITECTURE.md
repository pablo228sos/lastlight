# Physics and ML foundation

The implementation extends team commit `776caa4` from `feature/physics-api`;
that branch and the concurrent cinematic work are preserved. The base main was
`dadf01d`. No world geometry, site coordinates, assets or camera trajectories
are changed by this branch.

## Executable path

```text
strict SimulationRequest -> deterministic dispatch -> SimulationResult
                              |                           |
                    synthetic labels              generated TS wire types
                              |                           |
                   equipment-group splits        React scene adapter
                              |
              train-only normalization + logistic baseline + PyTorch MLP
                              |
                    checksum-verified checkpoint
                              |
                ML proposals -> independent physics verification
```

`services/simulation/schemas.py` is the authoritative physics wire schema.
`intelligence.py` and `forecast.py` define the additional strict API envelopes.
OpenAPI and `apps/web/src/lib/contracts.ts` are generated from the real service.
The overlapping camelCase simulation contracts were removed. React owns view
state and unit formatting, never a second dispatch algorithm.

## API

| Endpoint | Implemented result |
|---|---|
| POST `/api/v1/simulations` | Full physics summary, interval trace and replay metadata |
| POST `/api/v1/comparisons` | Existing battery/precharge comparison preserved |
| POST `/api/v1/fragility/predict` | ML estimate plus authoritative physics summary/trace; never ML clearance |
| POST `/api/v1/fragility/frontier` | Verified SoC × horizon map, optional ML estimates and re-simulated candidates |
| POST `/api/v1/forecast/load` | Working cold-start/hour-profile and historical/previous-week baselines |
| GET `/openapi.json` | Machine-readable contracts |

Physics uses kW, internal DC kWh, fractional SOC, UTC timestamps and elapsed
hours. Forecast inputs/outputs are hourly whole-building average kW. Forecasts
need an explicit critical/noncritical allocation before becoming physics input.

The simulation, prediction and frontier responses identify the physics version,
input hash, seed, provenance and assumptions. Prediction run identity also
includes the loaded ML version; `physics_run_id` identifies its physical run.
Forecasts explicitly have `physics_version: null`, a baseline model version and
research-derived provenance. They are estimates, not dispatch results.

The model is loaded lazily and checked against its checkpoint hash, feature
version and label-generating physics version. Missing/incompatible ML returns
physics with an explicit warning. `include_ml: false` is the frontier default:
rendering a physical map does not wait for a cold PyTorch import. Set it true to
receive separately marked proposals and up to twelve independently simulated
boundary candidates. Training never executes in an HTTP request.

## Frontier design and tradeoff

For fixed equipment and profile prefixes, failure within horizon is monotone in
that horizon. A full event-split physical run at one SoC therefore determines
every shorter horizon at that SoC. The displayed map uses this exact method.
Shorter cells carry null first-failure time when the event is not inside their
window. Grid restoration does not erase a previously observed critical failure.
Supplied profiles cannot be extrapolated beyond their declared duration.

The benchmark independently computes every grid point for reference. Uniform,
random and ML-guided samples get equal physical-call budgets and the same
nearest-neighbour reconstruction. ML reserves per-column endpoints and points
near its validation-selected classification threshold, then fills remaining
budget by score distance. This is an explicitly limited sampling strategy,
not a general claim about active learning. All reconstruction errors and missed
unsafe cells are reported. The exact prefix method is a further baseline.
Measured results favour the exact method; production displays no interpolated
ML region as verified physics.

## Frontend integration

DISCONNECT GRID requests the school scenario. A dedicated adapter derives
grid connectivity, noncritical light and critical-load light from the selected
row of the returned trace. The panel shows SOC, served demand, unserved energy,
observed first failure, an interval slider and verified frontier. Summary values
refer to the full run; instantaneous values refer to the selected row.

Reset, return and site changes invalidate in-flight responses. A new site starts
a new rehearsal; numerical results from the previous site are cleared. Other
archetypes remain explicitly synthetic. Backend failure removes numerical
results and states that only a visual rehearsal is available. The scene remains
one continuous WebGL world. Reduced-motion is retained.

## Boundaries

The dispatch is a quasi-static single-bus model, not certified electrical
network analysis. FragilityNet predicts synthetic scenario failure, not grid
outage occurrence. Its score and uncertainty flag cannot authorize equipment.
Every prediction endpoint performs physics, including out-of-domain inputs.
The OOD detector uses observed feature bounds; it does not prove joint-domain
coverage. A full neural EnergyDNA model, weather-conditioned demand training,
regional transfer validation and advanced active learning remain research work.
