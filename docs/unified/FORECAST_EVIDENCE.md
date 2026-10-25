# EnergyDNA evidence: cohort quality and the separate 12-hour experiment

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
| validation | persistence | 276 | 3312 | 17.9492 | 33.9306 | 17.6304 |
| validation | seasonal_day | 276 | 3312 | 6.6316 | 18.3821 | 6.5703 |
| validation | seasonal_week | 276 | 3312 | 7.0483 | 17.9491 | 7.0156 |
| validation | ridge | 276 | 3312 | 7.4717 | 15.5762 | 7.4102 |
| validation | direct_gru | 276 | 3312 | 6.8833 | 18.2486 | 6.8118 |
| test | persistence | 244 | 2928 | 13.3213 | 26.8256 | 13.1490 |
| test | seasonal_day | 244 | 2928 | 5.1929 | 13.6473 | 5.1551 |
| test | seasonal_week | 244 | 2928 | 6.9311 | 14.6676 | 6.8985 |
| test | ridge | 244 | 2928 | 6.3868 | 12.0041 | 6.3115 |
| test | direct_gru | 244 | 2928 | 5.4550 | 13.5429 | 5.4100 |
| generalization | persistence | 102 | 1224 | 2.7717 | 5.5612 | 4.2835 |
| generalization | seasonal_day | 102 | 1224 | 1.8827 | 3.9041 | 2.9096 |
| generalization | seasonal_week | 102 | 1224 | 1.8980 | 3.6623 | 2.9332 |
| generalization | ridge | 102 | 1224 | 2.1195 | 3.6771 | 3.2577 |
| generalization | direct_gru | 102 | 1224 | 1.8607 | 3.8548 | 2.8741 |

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
