# Battery Design Search — official physics only

**Reviewed feature:** [Draft PR #17](https://github.com/pablo228sos/lastlight/pull/17), on `physics/deterministic-design-search`, based on official verified `integration/release-candidate`. No changes to engine equations, ML, or frontend.

## API contract for Abai's Codex

`POST http://127.0.0.1:8000/api/v1/design-search` with `Content-Type: application/json`.

**Exact valid request** (saved in [design-search.request.json](examples/design-search.request.json)):

```json
{
  "scenario": {
    "duration_hours": 12,
    "step_minutes": 15,
    "grid": {"online": false},
    "load": {"critical_kw": 1.5},
    "solar": {"generation_kw": 0},
    "battery": {
      "initial_soc": 0.8,
      "minimum_soc": 0.2,
      "discharge_efficiency": 0.95
    }
  },
  "outage_target_hours": 12,
  "candidate_capacities_kwh": [24, 30, 32, 36]
}
```

The object in `scenario` is validated through the existing strict v1 `SimulationRequest`: all omitted fields receive the **existing official defaults**; capacity is the *only* field modified separately per candidate. In particular, the existing default 8 kW inverter, 8 kW battery discharge bound, noncritical load shedding, and non-islanding PV remain unchanged. Time is UTC and `battery.*soc` are **fractions** (0–1).

**Full exact output** depends on the official simulator's run UUID/input SHA; never fabricate these identifiers. Run the following against the real API to obtain and save the complete bitwise repeatable JSON, including `run_id`, hashes and full candidate data:

```bash
curl --fail-with-body -sS http://127.0.0.1:8000/api/v1/design-search \
  -H 'Content-Type: application/json' \
  --data-binary @docs/physics/examples/design-search.request.json \
  > docs/physics/examples/design-search.response.json
```

Or execute `python -m services.simulation.design_example` from repo root to print the complete actual JSON response with current default provenance; the Python example calls the same production function.

**Reference response values verified by regression tests** (projection of exact response; fields not listed here are still present in JSON):

```json
{
  "physics_model_version": "lastlight-dispatch-1.0.0",
  "outage_target_hours": 12.0,
  "candidate_count": 4,
  "selected_capacity_kwh": 32.0,
  "physics_verified": true,
  "candidates": [
    {"capacity_kwh": 24.0, "survived_target": false, "first_critical_failure_hours": 9.12},
    {"capacity_kwh": 30.0, "survived_target": false, "first_critical_failure_hours": 11.4},
    {"capacity_kwh": 32.0, "survived_target": true, "first_critical_failure_hours": null},
    {"capacity_kwh": 36.0, "survived_target": true, "first_critical_failure_hours": null}
  ]
}
```

These projected objects are **not** complete wire responses. The generated response contains additional exact fields `schema_version, run_id, input_hash, result_hash, seed, provenance, selection_rule, warnings` and each candidate's `valid, first_critical_failure_utc, unserved_critical_kwh, ending_soc, infeasibility_reasons, physics_run_id, physics_input_hash, comparable_cost`. Use the `*.response.json` saved with the curl command above for the complete response.

**Alternative input:** set `scenario.battery.initial_soc` to `1.0`, supply only `candidate_capacities_kwh:[24]`; the same official engine passes the 12 h outage with observed failure `null`. Do not merge these differing initial-SOC scenarios into one ranking.

## Acceptance and semantics

- Outage target must equal `scenario.duration_hours` exactly. Set the scenario's duration to the desired horizon instead of silently extrapolating profiles. Require `scenario.grid.online=false` and any grid profile entries all false: this is an **outage-only sizing** endpoint.
- 1..32 unique capacities, each finite number in 0.001..20,000 kWh; `candidates × scenario.interval_count <= 20_000`. Strict Pydantic types, forbidden extra keys, invalid fields return the existing structured **422 validation_error**. Profile lengths follow strict official simulation rules.
- Optional `comparable_costs`: one entry **per** capacity, `{capacity_kwh, amount, currency, basis}`. All entries must share currency and basis and amount must be nonnegative and finite. No local prices are provided or inferred.
- Response candidates are always sorted by capacity; the input list's order and cost array's order have no effect on `input_hash`, `run_id`, `result_hash`, or selection.
- Each candidate is simulated once by authoritative `engine.simulate()` with original grid, inverter, load, solar and SOC controls. `valid=true` means a capacity passed input validation and received a valid physics result, **not** that it survived the outage. Invalid request candidates are rejected as 422 rather than half-ranked.
- `survived_target` exactly mirrors official `SimulationSummary.survived_full_window`. The horizon interval is **[0, duration)**; an event exactly at the endpoint is **not observed**. `first_critical_failure_hours` and UTC are null when not observed; they are not an infinite-autonomy claim.
- `infeasibility_reasons` describe observed unserved critical demand and identifiable islanding/inverter limits, never guessed market hardware.
- `selected_capacity_kwh=null` when all supplied capacities fail; otherwise it is **the smallest passing candidate among this explicit set only**. No global optimum or market-price minimum. Costs are display annotations, not optimization.
- `physics_model_version, schema_version, seed, provenance` are inherited from the unchanged runtime. Per-candidate physics `run_id` and `input_hash` allow exact independent replay at `POST /api/v1/simulations`. Search-level `input_hash/run_id/result_hash` identify the normalized candidate set and its deterministic output.

## Integration boundary

- **Backend only** in PR #17. Do not modify PR #13's official frontend or numerical model.
- Abai may later call the new route from his Physics API adapter and display capacities, survival, unserved energy and SOC, with an explicit label **"smallest passing tested capacity"**.
- The frontend must show null observed first failure as *censored at 12 hours*, not as "never fails".
- UI must distinguish unavailable/invalid input (422), valid no-solution (200 with null `selected_capacity_kwh`), and success (200 with selected capacity).
- The existing `/api/v1/simulations`, `/api/v1/comparisons`, `/api/v1/frontiers`, live backend and Failure Frontier remain unmodified.

**CI evidence:** see PR #17 Checks → Physics API (Ubuntu & Windows same SHA) and `python -m services.simulation.check`. The production matrix also performs actual offline setup, live HTTP request, repeat, restart and shutdown. The local docs `docs/physics/openapi.json` are frozen to the actual FastAPI spec; fixture drift blocks CI.
