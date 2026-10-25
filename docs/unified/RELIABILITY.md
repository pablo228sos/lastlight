# FragilityNet reliability: fresh holdout and actual errors

The original PR19 900-case test has been inspected, including its 20 neural false
negatives (logistic 18). It is no longer pristine for new model selection. The
[preregistered protocol](RELIABILITY_PREREGISTRATION.md) was committed as
`70db480` before generating seed 20261025. Only original seed 20261024 train
(5,400) and validation (900) fit the new weights, normalization, temperature and
threshold. The 600 fresh test cases and 1,200 fresh equipment holdouts have no
input-hash or physical-signature overlap with the old dataset.

## Measured controlled comparison

One fixed 43/64/32/1 ReLU MLP: seed 20261025, AdamW .002, weight decay .001,
batch256, weighted BCE, max160epochs, patience20; actual47epochs. New features
add useful initial AC energy, grid restoration time, islanded demand/PV,
critical/requested energy deficits, inverter/discharge shortfalls and early/late
supply summaries. They use only resolved scenario inputs under explicit
simplifying assumptions, not dispatch outputs or labels. Scheduled PV/grid
profiles are synthetic scenario assumptions, not known real future conditions.
No individual feature's causal contribution is established without ablation.

The improved MLP's validation threshold .21 meets validation recall >=.99 and
precision >=.80 (recall .9911 / precision .9422). Thresholds use validation only.
The old MLP at its original .17 and logistic at .05 remain frozen comparators.
The .12 safety-threshold variant also uses validation, but fails the complete
promotion gate because of its false-positive tradeoff. None of the fresh test
scores was used for parameter or threshold tuning.

| Fresh group | Model | Recall | FN | Precision | F1 | PR-AUC | Brier | ECE |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| generalization (1200) | frozen_logistic | 0.9646 | 27 | 0.7880 | 0.8674 | 0.9671 | 0.11576 | 0.11351 |
| generalization (1200) | frozen_mlp | 0.9699 | 23 | 0.8831 | 0.9244 | 0.9875 | 0.05724 | 0.02204 |
| generalization (1200) | timing_mlp | 0.9817 | 14 | 0.9224 | 0.9511 | 0.9948 | 0.03837 | 0.01854 |
| generalization (1200) | timing_logistic | 0.9633 | 28 | 0.9351 | 0.9490 | 0.9920 | 0.04409 | 0.03612 |
| generalization (1200) | frozen_mlp_safety | 0.9817 | 14 | 0.8599 | 0.9168 | 0.9875 | 0.05724 | 0.02204 |
| test (600) | frozen_logistic | 0.9653 | 14 | 0.7831 | 0.8647 | 0.9623 | 0.11799 | 0.09499 |
| test (600) | frozen_mlp | 0.9530 | 19 | 0.8871 | 0.9189 | 0.9802 | 0.08288 | 0.05491 |
| test (600) | timing_mlp | 0.9653 | 14 | 0.9308 | 0.9478 | 0.9937 | 0.04643 | 0.02643 |
| test (600) | timing_logistic | 0.9505 | 20 | 0.9389 | 0.9446 | 0.9897 | 0.06067 | 0.05942 |
| test (600) | frozen_mlp_safety | 0.9653 | 14 | 0.8705 | 0.9155 | 0.9802 | 0.08288 | 0.05491 |

The timing MLP passes the predeclared recall/precision/FPR/F1/Brier gate on both
fresh groups. On test it matches logistic recall while improving precision; it
does not claim a recall advantage over logistic there. Against the frozen MLP,
test false negatives fall 19→14 and false positives 49→29; generalization falls
23→14 and 98→63. These are finite synthetic cohorts, not significance or field
safety guarantees. Test dangerous recall is lower than validation: errors remain.

The API now supports an explicit `lastlight-official-v1-features-2` request and
the website asks for that contract. `fragility-official-v1-timing-1eb5857a2421`
was registered only after reloading transformed saved weights and replaying all
1,800 fresh physical labels/features/metrics. The original 28-feature model and
default v1 API behavior remain available. A v2 request cannot silently load a v1
checkpoint. Physics always remains authoritative.

Weights SHA-256:
`1eb5857a2421501abcbb0c1a3205da6a4c68a295779fad405cfe747ae937dc0e`.
The new artifact includes train-only preprocessing, feature/source hashes,
temperature/threshold, fixed configuration, provenance and independent evidence.
The catalog pins the entire canonical manifest. Range-based OOD and threshold
margin warnings remain heuristics, not probabilistic confidence.

## All 20 original missed dangerous scenarios

Every row below was re-simulated. Diagnostic flags can overlap; they are not
invented exclusive causes. Eleven failed intervals have the battery at reserve;
nine have inverter and discharge power limits below critical demand. Sixteen
have no available solar at failure, one has PV present but blocked by islanding,
eighteen have the grid offline, five retain noncritical load. None is outside
the old marginal training feature ranges or within one step of the horizon.
This illustrates why a feature-range check does not prove generalization.

| Scenario ID | First failed interval h | Critical unserved kWh | Trace-supported flags |
|---|---:|---:|---|
| official-20261024-000237 | 10.921855 | 1.71850 | battery_at_minimum, solar_absent_at_failure, grid_offline_at_failure, noncritical_not_shed |
| official-20261024-000737 | 8.248819 | 2.55588 | battery_at_minimum, solar_absent_at_failure, grid_offline_at_failure |
| official-20261024-000777 | 0.000000 | 0.08051 | inverter_smaller_than_critical, discharge_limit_smaller_than_critical, pv_present_but_islanding_blocked, grid_offline_at_failure, noncritical_not_shed |
| official-20261024-001867 | 0.000000 | 2.60001 | inverter_smaller_than_critical, discharge_limit_smaller_than_critical, grid_offline_at_failure |
| official-20261024-001887 | 6.782930 | 4.88004 | battery_at_minimum, solar_absent_at_failure, grid_offline_at_failure, noncritical_not_shed |
| official-20261024-002007 | 0.000000 | 0.45745 | inverter_smaller_than_critical, discharge_limit_smaller_than_critical, grid_offline_at_failure, noncritical_not_shed |
| official-20261024-002387 | 0.000000 | 0.45102 | inverter_smaller_than_critical, discharge_limit_smaller_than_critical, solar_absent_at_failure, grid_offline_at_failure |
| official-20261024-002977 | 0.000000 | 0.12716 | inverter_smaller_than_critical, discharge_limit_smaller_than_critical, solar_absent_at_failure, grid_offline_at_failure, noncritical_not_shed |
| official-20261024-004007 | 14.512556 | 1.03192 | battery_at_minimum, solar_absent_at_failure, grid_offline_at_failure |
| official-20261024-004317 | 11.840085 | 3.28927 | battery_at_minimum, solar_absent_at_failure, grid_offline_at_failure |
| official-20261024-004837 | 0.000000 | 1.14313 | inverter_smaller_than_critical, discharge_limit_smaller_than_critical, solar_absent_at_failure, grid_offline_at_failure |
| official-20261024-006067 | 8.453987 | 4.63851 | battery_at_minimum, solar_absent_at_failure, grid_offline_at_failure |
| official-20261024-006077 | 0.000000 | 2.26063 | inverter_smaller_than_critical, discharge_limit_smaller_than_critical, solar_absent_at_failure, grid_offline_at_failure |
| official-20261024-006427 | 5.433709 | 0.93509 | battery_at_minimum, solar_absent_at_failure |
| official-20261024-006617 | 0.000000 | 2.70274 | inverter_smaller_than_critical, discharge_limit_smaller_than_critical, grid_offline_at_failure |
| official-20261024-006727 | 14.139796 | 2.29193 | battery_at_minimum, solar_absent_at_failure, grid_offline_at_failure |
| official-20261024-006927 | 3.661452 | 0.89022 | battery_at_minimum, solar_absent_at_failure, grid_offline_at_failure |
| official-20261024-007297 | 7.852658 | 2.57492 | battery_at_minimum, solar_absent_at_failure |
| official-20261024-007537 | 12.806214 | 3.45196 | battery_at_minimum, solar_absent_at_failure, grid_offline_at_failure |
| official-20261024-007697 | 5.250000 | 1.04404 | inverter_smaller_than_critical, discharge_limit_smaller_than_critical, solar_absent_at_failure, grid_offline_at_failure |

Full input, input hash, grid-restoration times, exact power/SOC intervals before
and at failure, and all flags are in
`research/reliability/artifacts/original-false-negatives.json`. The new model's
remaining 14 test and 14 generalization misses, with actual trace intervals, are
in `ml_bridge/artifacts/fragility-official-v1-timing/independent-evaluation.json`.

## Subgroups, calibration and reproducibility

`research/reliability/artifacts/comparison.json` reports each model separately
for inverter-below-critical, no-islanding, PV present, mixed grid schedules and
old-feature-range OOD subsets. Some overlap and some are one-class cohorts;
PR/ROC values are null when both labels are unavailable. Brier/ECE describe
synthetic label calibration, not real-world grid-outage probabilities. Raw
confusion matrices preserve every false positive and false negative.

Warm feature+score timings: old logistic .210 ms, old MLP .494 ms, timing logistic
.587 ms, timing MLP .814 ms; see `artifacts/latency.json` and
[complete workload timing](PERFORMANCE.md). More features cost time; no AI search
speed advantage is claimed.

Reproduce in order: `python -m research.reliability.prepare`,
`python -m research.reliability.compare`, `python -m research.reliability.register`,
`python -m research.reliability.benchmark`, `python -m research.reliability.report`.
The old dataset is regenerated with `python -m ml_bridge.generate --count 9000
--seed 20261024`. Raw Parquet is ignored; the versioned holdout manifest retains
seed, group capacities, counts, signatures and source identity. Re-executions
corrected report labels/serialization and reproduced the same weights; no new
hyperparameter selection followed the fresh evaluation.
