# FragilityNet timing-feature upgrade, official physics v1

Model: **fragility-official-v1-timing-1eb5857a2421**.
Weights SHA-256:
`1eb5857a2421501abcbb0c1a3205da6a4c68a295779fad405cfe747ae937dc0e`.
Feature contract: `lastlight-official-v1-features-2`, 43 input-only features.
Official label source remains `lastlight-dispatch-1.0.0`, schema `1.0.0`.
The original PR19 model is retained as the default for old v1 API requests.
The website explicitly requests the timing contract; mismatched models are
rejected, never relabelled. No PR7 physics/schema1.1 checkpoint is used.

## Target, training and fresh assessment

Predict whether a supplied synthetic scenario has observed critical failure
inside its exclusive observation window. This is not a measured outage model,
real-world outage probability or engineering clearance. Each integrated
assessment first executes the official physical simulation independently.

Original seed20261024 train5,400 / validation900 are unchanged; capacity groups
remain disjoint. The 900-case old test has already been inspected and is not
pristine for this experiment. [Protocol](../unified/RELIABILITY_PREREGISTRATION.md)
was committed at70db480 before generating seed20261025:600 test scenarios at
36kWh and1,200 equipment holdouts at30/42/60kWh. No signatures overlap old data.

The 43/64/32/1 ReLU MLP adds15 timing/energy/power summaries to the original28
features. Useful initial AC energy, demand before grid restoration, islanded
usable PV, critical/requested deficits and supply ordering use only requested
scenario inputs. They are approximate summaries under stated assumptions, not
another physical dispatch calculation. No target or physical trace is a feature.

Seed20261025; train-only mean/std; AdamW lr.002, decay.001, batch256, weighted
BCE, max160epochs, patience20. Actual47epochs, best validation BCE weights.
Temperature and threshold.21 use validation only. Validation recall.9911,
precision.9422. The fixed research configuration and all calibration values are
versioned with the actual checkpoint. No fresh-test tuning followed evaluation.

| Fresh assessment | Timing MLP | Frozen original MLP | Frozen logistic |
|---|---:|---:|---:|
| Test recall (600) | .96535 | .95297 | .96535 |
| Test false negatives | 14 | 19 | 14 |
| Test precision | .93079 | .88710 | .78313 |
| Test F1 | .94775 | .91885 | .86475 |
| Test PR-AUC | .99368 | .98020 | .96230 |
| Test Brier | .04643 | .08288 | .11799 |
| Generalization recall (1,200) | .98165 | .96986 | .96461 |
| Generalization false negatives | 14 | 23 | 27 |
| Generalization precision | .92241 | .88305 | .78801 |

It passes every predeclared recall/precision/false-positive/F1/Brier criterion
on both fresh groups, after independent saved-artifact replay. Recall only
matches logistic on fresh test; the gain there is precision/calibration. This
does not erase the original model's20 misses on its different900-case old test.

## Errors, deployment integrity and limits

All20 original missed cases were physically replayed with exact intervals:
11 at reserve,9 with inverter/discharge capacity below critical load; flags
overlap and include solar/grid restrictions. All28 remaining fresh timing-model
misses have IDs, hashes, outcomes and intervals in the new artifact's independent
evaluation. See [full comparison and trace report](../unified/RELIABILITY.md).
Subgroups include power/islanding/PV/grid schedule and feature-range OOD; Brier
and ECE calibrate only synthetic labels. No significance or field-transfer claim.

Loader checks actual official source/schema, explicit feature order/source,
finite normalization, weight checksum and canonical catalog-pinned manifest.
Original and timing checkpoints coexist. Missing, changed, corrupt or mismatched
artifacts leave physical results available. Every returned AI candidate is
separately simulated. Range and threshold-margin warnings are heuristics;
unsupported real equipment/locations remain unvalidated.

Actual web/API controls, tests and commands are in the [unified guide](../unified/README.md).
Weights/artifacts: `ml_bridge/artifacts/fragility-official-v1-timing/`.
Training/comparison/registration/replay: `research/reliability/`.
ML may suggest tests, never override physical conclusions or grant clearance.
