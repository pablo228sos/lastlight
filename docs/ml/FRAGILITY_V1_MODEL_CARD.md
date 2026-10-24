# FragilityNet: official-v1 research checkpoint

Model: **fragility-official-v1-8b40929366e6**. Weights: 18,621 bytes;
SHA256 `8b40929366e68b49abda5bfa75960e4b6ae9b3c74b28a1bb8ca24aa0d3728be1`.
This is a newly trained model, not a renamed PR #7 checkpoint.

## Purpose and authority

Classify critical-load failure within a supplied synthetic scenario window.
The score is conditional on simulation labels, not the probability of a real
city-grid outage. No model output authorizes equipment. Every assessment executes
the official deterministic simulator and returns its conclusion separately.

Official label source: `lastlight-dispatch-1.0.0`, schema `1.0.0`, PR #13 revision
`479e8d1`. The observed interval is exclusive at its right endpoint. All 1/15/60
minute tests survive at 9.12 hours and fail at 9.120001 hours for the reference.

## Data and features

9,000 reproducible synthetic scenarios, generator seed 20261024, dataset identity
`a69ad7a4034284139eaec0a0d5af9a61ec6603bd49285f300cd27cb662d567c8`.

| Split | Rows | Dangerous cases | Battery capacities kWh |
|---|---:|---:|---|
| Train | 5,400 | 4,016 | 6, 12, 24, 48 |
| Validation | 900 | 674 | 18 |
| Independent test | 900 | 593 | 36 |
| Generalization | 1,800 | 1,152 | 30, 42, 60 |

Whole capacity groups are disjoint, not merely shuffled rows. Input and physical
signatures are unique. No measured failures or Kyrgyzstan meter data are used.
Raw Parquet remains ignored. Every row stores replay inputs, source/schema/hash,
seed, feature contract, outcome and synthetic provenance.

The 28 input-only features are ordered in `ml_bridge/features.py`, contract
`lastlight-official-v1-features-1`. They cover storage, limits/efficiency, constant
loads, supplied PV/grid statistics, outage length, topology/control flags and
start time. They contain no simulator outcome. Temporal statistics compress
profile ordering and can alias different dispatch histories.

Generator ranges: capacities above; inverter 2/4/6/8/12 kW (held-out 3/7/11),
critical demand 0.4–6 kW with 2% zero-demand edge cases, noncritical 0–5 kW,
initial SOC 0.3–1 with 5% minimum-SOC edge cases, minimum 0.1/0.2/0.25,
efficiencies 0.88–0.98, horizon 4/8/12/16/24 h, step 15 min, synthetic PV peak
0/2/5/10 kW with cloud factors 0.3/0.65/1. Grid states include outage, online,
restoration and outage onset; import limits 2/5/10/20 kW. Grid charging appears
in 15% of scenarios. These are bounded research assumptions, not equipment specs.

## Training and selection

Compact PyTorch 28→64→32→1 ReLU MLP, AdamW lr 0.002/weight decay 0.001,
batch 256, max 240 epochs, patience 20. The completed run took 49 epochs. Seed 20261024,
deterministic CPU training. Normalization fits train only. Weights select on
validation BCE; temperature calibration and F2 threshold select on validation
only. The saved normalizer, baseline coefficients, temperatures, thresholds,
actual library environment and full training configuration are in the manifest.

A 3,000-row pilot was compared before choosing 9,000 rows: validation MLP F1
0.9247→0.9493 and Brier 0.05873→0.04927; dangerous recall 0.9908→0.9866.
Independent test labels were not used for this choice or threshold selection.
Cross-platform exact retraining bits are not promised; the released checkpoint
is fixed, checksum-verified and independently replayed.

## Actual independent metrics

| Split/model | Accuracy | Precision | Dangerous recall | F1 | PR-AUC | Brier | False negatives |
|---|---:|---:|---:|---:|---:|---:|---:|
| Test logistic | .7989 | .7791 | .9696 | .8640 | .9712 | .10317 | 18 |
| Test neural | .8922 | .8815 | .9663 | .9220 | .9871 | .06447 | 20 |
| Generalization logistic | .8344 | .8144 | .9601 | .8813 | .9715 | .11357 | 46 |
| Generalization neural | .9206 | .9078 | .9748 | .9401 | .9901 | .05600 | 29 |

The neural model improves F1/PR-AUC/calibration here, but **test dangerous recall
is slightly worse than logistic: 20 missed dangerous cases versus 18**. It does
not uniformly dominate the baseline. Logistic remains available; choose it when
this experiment's test recall is the criterion. Neither may override physics.
No threshold was retuned after seeing the independent test.

Full confusion matrices, ROC-AUC, ECE, thresholds, trace-derived false-negative
diagnostics and replay inputs are in
[independent-evaluation.json](../../ml_bridge/artifacts/fragility-official-v1/independent-evaluation.json).
All 9,000 labels/features/outcomes were replayed by official physics before the
catalog entry was produced. False-negative diagnostics distinguish minimum SOC,
islanding and insufficient available power; these are trace heuristics.

## Deployment bounds

Feature-range OOD detection and proximity to the fitted threshold are conservative
heuristics, not statistical uncertainty guarantees. Legal official inputs can
lie outside the synthetic training range; e.g. the official 50 kW grid-import
default exceeds the observed 20 kW maximum, even if the grid is currently offline.
Such warnings preserve the official answer and do not grant model clearance.

Only catalog-matching checkpoints load in the online adapter. Offline training
and evaluation may inspect proposed checkpoints with an explicit bypass; the
HTTP API exposes no such option. Catalog registration means independent research
replay, not peer approval or electrical certification. See the handoff for the
optional router and reviewed integration boundary.
