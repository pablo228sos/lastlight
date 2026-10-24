# Deterministic battery capacity design search

`POST /api/v1/design-search` enumerates an explicitly supplied finite set using
the official `simulate()` engine. It selects the **smallest tested capacity
that serves all requested critical load throughout the tested outage**. All
candidates are simulated, including those above the first passing candidate.
No new dispatch equations, monotonicity shortcut, ML model, hardware catalogue,
continuous minimum or market-cost optimisation is involved.

Implementation: `services/simulation/design_search.py`. Base release:
`479e8d1fdbb0c357f61468c8934a314f345a15ed`, Draft PR #13. The engine and existing
simulation schemas/fixtures remain unchanged. The new route has typed request
and response schemas in [OpenAPI](openapi.json); existing v1 routes retain their
contracts. Search version is `lastlight-battery-search-1.0.0`; physics model is
`lastlight-dispatch-1.0.0`; official simulation schema is `1.0.0`.

## Request

This minimal JSON produces the exact checked-in reference response:

```json
{
  "scenario": {},
  "outage_hours": 12,
  "candidate_capacities_kwh": [24, 30, 32, 36]
}
```

`scenario` is required and uses the existing strict `SimulationRequest`.
`{}` resolves its official defaults: initial SOC .8, reserve .2, maximum SOC 1,
discharge efficiency .95, critical load 1.5 kW, noncritical 2 kW shed during
outage, no PV/grid, 8 kW inverter and discharge limit, 15-minute steps, 12-hour
duration and fixed synthetic UTC start. Default scenario capacity 24 kWh is
replaced separately for each candidate; other battery constraints stay fixed.

| Field | Validation / meaning |
| --- | --- |
| `scenario` | A valid official request, including all nested constraints and complete original profile lengths. Invalid values are rejected even if a candidate would replace them. No v1.1 demand-profile extensions. |
| `outage_hours` | Required finite number, 1/60–168 hours, no greater than `scenario.duration_hours`. Tests the prefix starting at `scenario.start_utc`; there is no start-offset search. |
| `candidate_capacities_kwh` | Required JSON array of 1–32 unique finite numbers, .001–20,000 kWh each. Strings, booleans, duplicates and invalid entries are rejected, not silently skipped. |
| Work budget | `len(candidates) × ceil(outage_hours × 60 / step_minutes) <= 20,000` base intervals. The existing engine may event-split those intervals. |
| Grid | The effective grid state must be offline throughout the target. A supplied profile takes precedence over the constant flag, as in the official engine. Grid states outside the target are not tested. |
| Profiles | Validated against the original scenario, then sliced to cover the target prefix, including a final partial interval. No extrapolation, padding, interpolation or invented weather. |
| `costs` | Optional or null. If supplied, must cover exactly the candidate set with unique entries, one common currency label and one common basis. Costs never change the selection rule. |

Unknown fields, malformed JSON and nonfinite numbers receive the existing
structured **422** error envelope. Invalid searches make no simulator calls.
All candidates must be valid before evaluation starts. Physical infeasibility
is different: a valid search with no passing candidate returns **200** and
`status="no_feasible_candidate"`, with both selected fields null. An internal
engine invariant failure aborts the entire request with the existing **500**
`energy_balance_error`; it is not skipped or labelled a feasible design.

The target changes the duration to the declared outage prefix. Only candidate
capacity changes within that prefix; inverter power/islanding, charge/discharge
kW, SOC fractions, efficiencies, loads and PV assumptions remain fixed.
Increasing capacity therefore also increases initial stored kWh at the same
SOC fraction. It does **not** automatically increase inverter or battery kW.

## Response contract for Abai's Codex

| Field | Integration rule |
| --- | --- |
| `status` | `feasible_candidate_found` or `no_feasible_candidate` |
| `selection_rule` | Always `smallest_passing_capacity_in_candidate_set` |
| `selected_capacity_kwh` | Smallest passing **listed** capacity; null when none pass |
| `selected_simulation_run_id` | ID of that candidate's official simulation; null when none pass |
| `candidates` | Sorted ascending by capacity, regardless of input order |
| `candidates[].valid` | True means the simulation request validated and executed; it is not installation certification |
| `candidates[].feasible` | Taken directly from official `summary.survived_full_window`; critical-load service only |
| `candidates[].infeasibility_reasons` | Empty for a survivor; otherwise `critical_shortfall_within_outage`. This describes the observed outcome, not a guessed equipment fault |
| `candidates[].summary` | The **unaltered official SimulationSummary**, including `critical_survival_hours`, `first_failure_utc`, `unserved_critical_kwh`, `ending_soc` and energy accounting |
| `candidates[].input` | Fully resolved official SimulationRequest for the tested target and capacity; post this to `/api/v1/simulations` to retrieve the full event-split trace |
| `candidates[].simulation_run_id`, `simulation_input_hash` | The actual official result identifiers, not search-generated substitutes |
| `candidates[].simulation_result_hash` | SHA-256 of the complete official result, including every event-split trace interval, for replay verification |
| `candidates[].model_version`, `schema_version`, `provenance`, `warnings` | Copied from the actual simulation; no ML provenance is implied |
| `candidates[].cost_amount` | User-provided total in the common declared currency/basis, or null |
| `physics_calls` | Actual number of candidates evaluated; no early exit |
| `search_id`, `input_hash`, `result_hash` | Deterministic search identity, canonical request hash and response hash |

**Do not display `idealized_autonomy_hours` as an observed event.** A null
`critical_survival_hours` means no critical shortfall inside the exclusive
target window, not infinite autonomy. Reaching reserve exactly at the endpoint
passes; a positive shortfall interval before the endpoint fails. Noncritical
shedding/degraded state alone does not disqualify critical-load survival.
An observed value of `0.0` is an immediate failure; check for null explicitly,
not JavaScript truthiness.

After selection, replay `candidate.input` through `/api/v1/simulations` and use
that returned trace for SOC, actual start/end timestamps and scene power states.
Confirm its `run_id` and `input_hash` against the candidate identifiers. Existing
baseline/comparison/frontier endpoints and offline UI fixtures are unchanged.
**No design-search UI or saved design replay is added to the frontend in this PR.**

## Exact examples and observed reference results

The following files are generated from actual HTTP responses by
`python -m services.simulation.fixtures` and checked locally and in production
CI. They are complete JSON examples, without omitted fields or placeholder IDs:

- [Resolved reference request](fixtures/design-search.request.json) →
  [exact reference response](fixtures/design-search.result.json).
- [24 kWh / SOC 100% request](fixtures/design-search-precharge.request.json) →
  [exact precharge response](fixtures/design-search-precharge.result.json).
- [Request JSON Schema](design-search-request.schema.json),
  [response JSON Schema](design-search-result.schema.json).

For the reference request, at a 12-hour horizon:

| Capacity | Observed critical failure | Critical unserved kWh | End SOC | Pass |
| --- | --- | --- | --- | --- |
| 24 kWh | 9.12 h | 4.32 | 20% | No |
| 30 kWh | 11.4 h | .9 | 20% | No |
| 32 kWh | null | 0 | ≈20.7895% | Yes — selected |
| 36 kWh | null | 0 | ≈27.3684% | Yes |

24 kWh at initial SOC 100% also passes 12 h; its 12.16 h analytical reference
is observed only in the separate 16-hour regression. Existing 9.12/13.68/12.16 h
16-hour regressions remain intact. With a 1 kW inverter and 1.5 kW critical
load, even 20,000 kWh fails at time zero: capacity cannot fix inadequate power.

Start the existing local server in one terminal, then from repository root:

```bash
curl -sS http://127.0.0.1:8000/api/v1/design-search \
  -H 'Content-Type: application/json' \
  --data-binary @docs/physics/fixtures/design-search.request.json
```

PowerShell:

```powershell
$design = Invoke-RestMethod http://127.0.0.1:8000/api/v1/design-search -Method Post -ContentType application/json -Body (Get-Content -Raw docs/physics/fixtures/design-search.request.json)
$design.selected_capacity_kwh
$candidate = $design.candidates | Where-Object capacity_kwh -EQ $design.selected_capacity_kwh
$trace = Invoke-RestMethod http://127.0.0.1:8000/api/v1/simulations -Method Post -ContentType application/json -Body ($candidate.input | ConvertTo-Json -Depth 20)
$trace.summary
```

Optional cost shape: `costs` contains `currency` (three uppercase ASCII letters),
`basis` (nonblank, at most 200 characters), and `entries`, each with
`capacity_kwh` and finite nonnegative `amount` <= 1e12. Every listed capacity
must have exactly one total. These are user-declared comparable totals; currency
registration, taxes, equipment content and quote accuracy are not verified.
A cheaper larger candidate does not override the smallest passing capacity.
No equipment prices or local quotations are supplied by the service.

## Determinism, verification and scope

Candidate/cost ordering is canonicalised before hashing and evaluation. Defaults,
UTC-normalised timestamps, seed, provenance and cost declarations enter the
resolved search input. `search_id` is UUID5 in `NAMESPACE_URL` using
`design-search:{search_version}:{model_version}:{input_hash}`.

Hashes use the existing Python-style canonical JSON convention:
`json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)`
(default `ensure_ascii=True`), encoded as UTF-8, then SHA-256. `result_hash`
excludes only itself. `simulation_result_hash` includes the **entire** official
simulation result. Plain JavaScript `JSON.stringify` is not this canonicaliser
(notably float/Unicode representation); browser integrations should verify the
official IDs, or use the documented Python hash convention for full replay.

```bash
python -m services.simulation.check
python -m pip download --require-hashes -r services/simulation/requirements.lock -d /path/to/wheels
python -m services.simulation.integration_check --wheelhouse /path/to/wheels
```

The full check covers ranking, all input permutations, comparable costs,
strict invalid input, work limits, no survivor, exact boundary, 1/7/15/60-minute
steps, solar/islanding, profile truncation, unchanged power/SOC constraints,
parallel determinism, full-result replay and existing frontier behaviour.
The real HTTP probe now checks design selection, every candidate's full trace
hash, precharge survival and the existing frontier on both offline starts.
The inherited Ubuntu/Windows Python 3.12 workflow runs both verification commands;
actual results for this branch are linked in its Draft PR.

Local Linux verification on 24.10.2026, Python 3.12.14: **193 tests passed**,
99.58% combined statement coverage (engine/schemas/API/search), search module
100% statement coverage; all **18** generated contract/fixture files verified.
The fresh-installer/HTTP/offline probe passed **26 checks**, with exit code 0
and a released server port after both starts. The search result hash matched
before and after restart. Existing OpenAPI paths/components, original engine,
simulation schemas, frontier, launchers, dependency locks and 11 original
schema/fixture files are unchanged; only the OpenAPI document gains the route
and new types. These Linux results are not a substitute for the two OS CI jobs.

This is a capacity-only scenario search. It does not establish a continuous
minimum, a globally cheapest installation, equipment availability, AC-network
safety or field accuracy. 32 kWh is the answer **within the four tested
capacities and declared assumptions**; real design margins and measured load
profiles remain engineering inputs.
