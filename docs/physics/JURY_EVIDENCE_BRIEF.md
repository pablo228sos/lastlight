# LASTLIGHT — Jury Physics Evidence Brief (reviewed update)

**As of 2026-10-24.** This evidence snapshot corrects the earlier claim that native Windows shutdown / production CI was blocked. No changes are made here to the earlier research/competitor/sensitivity work in PR #12.

## Verified official integrated release candidate

- Official integration: [Draft PR #13](https://github.com/pablo228sos/lastlight/pull/13), branch `integration/release-candidate`, verified release SHA `479e8d1fdbb0c357f61468c8934a314f345a15ed`.
- [Physics API production matrix run 40096664592](https://github.com/pablo228sos/lastlight/actions/runs/40096664592) **SUCCESS on both Ubuntu and Windows for the same head SHA**; this includes the official Python check and fresh installer, live localhost HTTP, offline restart and graceful shutdown.
- [Verify run 40096664610](https://github.com/pablo228sos/lastlight/actions/runs/40096664610) also **SUCCESS** for the same SHA. Thus the earlier PR #11 Windows shutdown issue is **already resolved in PR #13**. Do not describe it as an open blocker.

## New engineering candidate: deterministic design search

- [Draft PR #17](https://github.com/pablo228sos/lastlight/pull/17), isolated branch `physics/deterministic-design-search`, directly based on the verified PR #13 branch. Not merged into PR #13 or `main`.
- Implements strict `POST /api/v1/design-search` via the unchanged official `engine.simulate()`; evaluates each explicit candidate on a true outage and selects the smallest candidate that passes the tested *exclusive* horizon. Invalid/infeasible are not confused.
- Regression: with 12 h, 1.5 kW critical demand, 80% starting SOC, 20% reserve, 95% discharge efficiency and no solar, the supplied capacities `[24,30,32,36]` have observed failure `[9.12h,11.4h,null,null]`; the selected **smallest passing candidate in this set** is **32 kWh**. A separate scenario with 24 kWh fully precharged to 100% survives the 12 h horizon.
- Optional costs are *user-supplied annotations* on an identical currency and cost basis. No market quotes or global optimality are asserted.
- The complete new endpoint contract, request and machine-generated exact response command are [documented for Abai](DESIGN_SEARCH.md). OpenAPI is frozen at [openapi.json](openapi.json).

### Independent verification gates

- Prior fully passing code commit `a0d481764d4e771c9fe7327013720291a44975f9`: [official Ubuntu+Windows Physics API matrix 40115138224](https://github.com/pablo228sos/lastlight/actions/runs/40115138224) **SUCCESS** on both platforms; this checks the design-search regression tests, original frozen routes, generated OpenAPI and actual live API.
- After final docs/tests are committed, **only claim the final SHA if the final build's Ubuntu and Windows jobs both pass**. PR #17 remains Draft and is not production until reviewed and merged. The production candidate PR #13 remains unmodified.

## Jury-safe explanation

> We use a deterministic, openly constrained energy-balance model to evaluate several battery capacities under a specified outage and critical-load profile. Each capacity runs the authoritative simulator. In our synthetic, constant-demand 12-hour reference, 32 kWh is the smallest passing capacity **among four tested candidates**; this is not a global optimal design or a hardware procurement quote. A successful 12-hour result means no critical failure was observed *within that window*, not that the battery lasts forever.

## Outstanding limits

- Synthetic model, not site-measured telemetry. Model excludes voltage/frequency and battery aging/thermal/transient effects; details in [MODEL.md](MODEL.md).
- No vendor specification, verified installed cost, or calibration to a real school; user-provided costs are comparable only if input conditions genuinely match.
- No new ML model and no changes to physics equations or v1 simulation/comparison/frontier behavior.
- Abai retains final integration authority; the official Physics-API-connected UI in PR #13 must not silently switch to unreviewed calculations.
