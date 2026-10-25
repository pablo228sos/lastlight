# LASTLIGHT unified intelligence: evidence for judges and reviewers

The actual school application now calls one backend for deterministic physics,
FragilityNet and the clearly separated EnergyDNA research preview. This is an
integration of trained artifacts, not predictions embedded in React.

## Implemented and integrated

| Capability | What the judge can do | Source of the result |
|---|---|---|
| Official physics | Select school, disconnect grid, scrub the physical trace, compare capacity or precharge, switch 12/16 h windows | Unchanged `lastlight-dispatch-1.0.0`, schema `1.0.0` |
| FragilityNet | Run AI resilience analysis on the exact active input | Verified PyTorch timing MLP; separate neural identity, warnings and synthetic-label score |
| Failure Frontier | Inspect physical cells, ask AI to suggest cases, inspect independently checked markers | One physical trace per charge column; each selected AI case also gets its own physical run |
| EnergyDNA preview | Run an actual one-hour GRU and compare with persistence and recorded history | Three packaged, source-hashed, attributed BDG2 examples; target never enters inference |

Physics determines whether critical demand is served. For the reference 24 kWh,
80% initial charge, 20% reserve, 1.5 kW critical load and zero PV, unmet critical
demand begins at **9.12 h**. An observation window ending exactly there survives
under the exclusive `[0,horizon)` semantics. Extending the outage observes the
failure. The lighting still follows the original physical trace.

FragilityNet predicts a **synthetic scenario failure label**, not the chance of
a real city outage. Its original PR19 model trained on 5,400 official labelled
scenarios, with 900 validation targets and capacity-group holdouts. The new
43-feature timing model uses those same train/validation partitions, input-only
energy/power/timing summaries, and a fresh preregistered 1,800-scenario holdout.
On the fresh 600-row test, its dangerous recall is **96.53%**, precision **93.08%**,
F1 **.9478**; **14 false negatives remain**. Frozen PR19 MLP: recall 95.30%,
precision 88.71%, F1 .9189 and 19 false negatives. Frozen logistic also misses
14: the new MLP matches its recall while improving precision. See the complete
[reliability report](RELIABILITY.md), calibration/subgroups and trace evidence.

The frontend explicitly requests `lastlight-official-v1-features-2` and identifies
`fragility-official-v1-timing-1eb5857a2421`. Legacy API requests default to the
unchanged original PR19 model. The incompatible PR7 1.1 model is never loaded.
Missing/corrupted/mismatched ML produces an unavailable warning; the physical
calculation and physical map remain usable. A warm cache also detects changed
checkpoint bytes. No neural score or candidate grants engineering clearance.

EnergyDNA predicts **one-hour whole-building average electrical demand** from
past load/masks and known calendar inputs. Its genuine 1,377-parameter GRU loses
to persistence on one-hour test MAE: **4.1866 versus 3.9336 kW**, although its
RMSE is lower (7.4530 versus 8.8408). Persistence remains preferred. BDG2 is
overseas historical building data, not Kyrgyz critical-circuit measurements.
The preview displays recorded targets only as retrospective comparisons.

## Implemented but research-only

- A separately trained direct **12-hour** GRU, with complete-horizon/per-hour and
  per-building evaluation. Test MAE 5.4550 kW versus yesterday's profile 5.1929;
  the daily baseline remains preferred. It does not replace the one-hour UI.
- A typed, tested [forecast allocation proposal](FORECAST_TO_PHYSICS.md), with
  explicit provenance, timestamp, units, gaps, uncertainty and reviewed circuit
  allocation. It deliberately refuses conversion to the constant-load v1 schema.
- New model comparisons/calibration and all 20 original false-negative traces.
  No statistical significance, field validation or electrical certification.

## Planned, not implemented

Measured Kyrgyz building validation, available-at-origin weather forecasts,
seasonal/multi-year transfer, calibrated forecasting intervals and a separately
versioned dynamic-load physics extension. A future local study must distinguish
whole-building and critical/noncritical circuit meters, document kWh integration
and clocks, retain gaps, and reserve chronological/building holdouts before
fitting. None of those measurements or approvals is claimed here.

See [forecast evidence](FORECAST_EVIDENCE.md), [actual latency measurements](PERFORMANCE.md),
[reproduction](README.md) and the [two-minute demo](DEMO_SCRIPT.md).
