"""Render measured report tables from versioned numerical evidence."""

import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    report = json.loads(
        (root / "research/reliability/artifacts/comparison.json").read_text()
    )
    errors = json.loads(
        (
            root / "research/reliability/artifacts/original-false-negatives.json"
        ).read_text()
    )
    text = """# FragilityNet reliability: fresh holdout and actual errors

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
"""
    for split, models in report["splits"].items():
        for name, values in models.items():
            m = values["global"]
            text += f"| {split} ({m['n']}) | {name} | {m['dangerous_recall']:.4f} | {m['false_negatives']} | {m['precision']:.4f} | {m['f1']:.4f} | {m['pr_auc']:.4f} | {m['brier_score']:.5f} | {m['ece_10_bins']:.5f} |\n"
    text += """
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
"""
    for case in errors["cases"]:
        flags = ", ".join(k for k, v in case["flags"].items() if v)
        m = case["physical_summary"]
        text += f"| {case['scenario_id']} | {m['critical_survival_hours']:.6f} | {m['unserved_critical_kwh']:.5f} | {flags} |\n"
    text += """
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
"""
    (root / "docs/unified/RELIABILITY.md").write_text(
        text, encoding="utf8", newline="\n"
    )
    forecast = json.loads(
        (root / "research/energydna/artifacts/direct12-v1/evaluation.json").read_text()
    )
    text = """# EnergyDNA evidence: cohort quality and the separate 12-hour experiment

The unchanged one-hour GRU remains in the application research preview, with
its preferred persistence baseline: test MAE 4.1866 versus 3.9336 kW, RMSE
7.4530 versus 8.8408 kW. See the [original card](../ml/ENERGYDNA_MODEL_CARD.md).
The preview runs weights on request; only source-hashed observations/retrospective
targets are packaged, not predictions. Three readable examples are demonstrations,
not a newly selected evaluation cohort.

## Cohort audit

Same 12 pinned BDG2 IDs, 90 raw-data days, chronological 54/18/18-day periods,
7/2/3 building groups. `Swan_unknown_Isaiah` is entirely missing; no targets are
invented. `Hog_education_Cathleen` is all zero. `Panther_parking_Lorriane` has
2,154 zeros in 2,160 hours, making it a near-zero control. The other buildings
include lodging, warehouse, education, health, science and assembly uses with
very different load magnitudes. Raw zeros and abrupt meter changes are not proof
of actual operating behavior; they can include meter faults. No difficult
building was silently deleted and no future anomaly filter changed old targets.

`research/energydna/artifacts/direct12-v1/cohort-quality.json` records each ID's
coverage, zeros, mean/p99 magnitude, usage and largest hourly change. These are
descriptive full-period audit values; they are never input normalization or
retrospective target-cleaning rules. Missing/invalid inputs remain causally
handled; targets are never imputed. No weather has been added: a reviewed
time/availability alignment is absent, and realized future weather is not an
acceptable forecast input.

## Direct 12-hour experiment

A separate 2,540-parameter GRU sees the preceding **168 hours** of past load and
masks, known origin calendar features, and twelve **past-day** hourly references.
It outputs twelve values directly; no actual future load enters any input or
recursive step. Origin stride is 12 hours. A complete target horizon and known
day/week reference are required for every method. Train/validation boundary
origins are purged unless the whole 12-hour target stays inside its partition.
Building holdouts and training-only Ridge scaling are preserved.

One fixed run: seed20261026, GRU16, head36/32/12, AdamW .001, decay .001,
batch64, SmoothL1 on past-history-scaled targets, clip1, max80epochs, patience10.
Actual11epochs; best validation epoch1 has nonzero weight updates. Early stopping
and method selection use validation macro-building history-scaled MAE only.
The model does not win that criterion; previous-day seasonal naive remains
preferred. No architecture was tuned on test results.

| Group | Method | Origins | Evaluated target hours | MAE kW | RMSE kW | Nonconstant-building macro MAE kW |
|---|---|---:|---:|---:|---:|---:|
"""
    for split, models in forecast["metrics"].items():
        for name, m in models.items():
            text += f"| {split} | {name} | {m['origins']} | {m['target_hours']} | {m['mae_kw']:.4f} | {m['rmse_kw']:.4f} | {m['nonconstant_macro_mae_kw']:.4f} |\n"
    text += """
Every method uses identical eligible complete targets. The generalization group
includes a constant-zero control; the nonconstant column removes that control
from the descriptive macro average, and per-building scores preserve it. The
12-hour GRU slightly improves generalization aggregate MAE over daily naive,
but loses the predefined validation criterion and test MAE. Selection stays
with the daily baseline. Results cannot be compared directly to the one-hour
cohort as a horizon-invariant accuracy claim.

Per-horizon errors for all twelve hours, per-building errors, validation history,
source manifest, source/weight hashes, Ridge coefficients and scaler are in
`research/energydna/artifacts/direct12-v1/`. Reload of the saved weights reproduces
test predictions exactly. Repeated fixed-configuration training reproduced
`energydna-direct12-v1-54726a24a6f8`; no test tuning. Reproduce with
`python -m research.energydna.multihour` after the same bounded downloader.

This mode remains research-only and is not selected by the website or injected
into the physics API. The working one-hour checkpoint is preserved. All derived
BDG2 examples/artifacts retain the [attribution and share-alike terms](../../research/energydna/NOTICE.md).
Naive source-local clocks, meter faults, the short season and small building
cohort limit transfer claims. No Kyrgyz critical-load or multi-year validation,
weather forecasting or calibrated uncertainty interval is claimed.
"""
    (root / "docs/unified/FORECAST_EVIDENCE.md").write_text(
        text, encoding="utf8", newline="\n"
    )
    print("Rendered reliability and forecast evidence from actual versioned reports")


if __name__ == "__main__":
    main()
