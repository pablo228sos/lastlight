# EnergyDNA-Net: measured one-hour BDG2 prototype

The unified application now runs this same one-hour checkpoint in its separate
historical research preview. [Updated cohort/12-hour evidence](../unified/FORECAST_EVIDENCE.md)
describes the additional direct-horizon experiment; it does not replace this
artifact, its one-hour horizon or its preferred persistence baseline.

## Intended use and measured conclusion

`energydna-gru-v1-56d366ec3532` is a genuinely trained 1,377-parameter PyTorch
GRU for **one-hour-ahead whole-building electricity forecasting**. It improves
on the weekly seasonal-naive baseline, but **does not beat persistence on MAE**.
Persistence was selected on validation and remains the preferred method for
this experiment. The GRU's lower test RMSE does not override that predefined
MAE-based selection. This demonstrates a working neural forecasting experiment,
not production forecasting approval.

Nothing connects this forecast to the official physics API or emergency load
profiles. Overseas whole-building loads do not establish demand of Kyrgyz
schools or critical circuits. No weather features or geographic transfer
validation are claimed.

## Source and cohort

- BDG2 commit `9b97ccbe90096aff42ed4fd6493bf7ae692d7118`.
- Same twelve building IDs as PR #7; first **2,160 hourly rows**, January 1
  through March 30, 2016: 25,920 building-hours.
- Raw `data/meters/raw/electricity.csv`, rather than the earlier cleaned file.
  The pinned [cleaning notebook](https://github.com/buds-lab/building-data-genome-project-2/blob/9b97ccbe90096aff42ed4fd6493bf7ae692d7118/notebooks/10_Cleaned-dataset.ipynb)
  applies whole-series anomaly detection and zero-gap filtering. We avoid those
  retrospective target filters. Raw sensor faults and zeros remain limitations.
- Local subset SHA-256:
  `7d910a7e31289e1fd0e94139574164d7dd3201e96a9e064cf51dfb1543675ac6`.
  Metadata SHA-256:
  `992d0b29f24f96ad4332bc4dbb534b7bdd7dd2689aad093f94e93068ecddca02`.
- The [dataset authors' paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7591488/)
  identifies the raw energy meters as hourly kWh sums with local timestamps.
  Hourly electrical kWh / 1 hour gives average kW for that interval. The source
  local hourly labels are retained, without claiming UTC conversion or a
  resolved DST alignment. No weather or cross-site timestamp join is performed.
- 2,184 missing readings; zero negative/nonfinite nonmissing readings.
  `Swan_unknown_Isaiah` has no observations and contributes no eligible windows.
  `Hog_education_Cathleen` is entirely zero and remains an explicit control.
  `Panther_parking_Lorriane` has 2,154 zeros in 2,160 rows. These data cannot
  establish broad forecasting skill across normal building operations.

The nested `data.source` in the artifact manifest is the complete source
manifest, with exact URLs, IDs, checksums, units, selection and attribution.
Raw data stays ignored. See [attribution and derived-artifact license](../../research/energydna/NOTICE.md).

## Temporal and building separation

Buildings are sorted and permuted with seed `20261024`, fixed before fitting:

| Group | IDs |
|---|---|
| Train (7) | Eagle_health_Amy, Peacock_lodging_Mathew, Panther_parking_Lorriane, Lamb_education_Emery, Robin_lodging_Celia, Bull_lodging_Leonard, Mouse_science_Micheal |
| Validation-only (2) | Fox_warehouse_Lorretta, Swan_unknown_Isaiah (no eligible readings) |
| Generalization (3) | Hog_education_Cathleen (zero control), Rat_assembly_Francine, Rat_assembly_Silvia |

Train targets end before **2016-02-24 00:00** (54 days). Validation targets are
February 24 through March 12 (18 days), drawn from the seven training IDs plus
validation-only IDs. Independent test targets are **March 13–30** (18 days):
training buildings and generalization IDs are reported separately. Model and
Ridge coefficients/scaler fit only the training IDs in the first period.
Validation-only IDs may influence early stopping and method selection, never
weight gradients. Generalization IDs influence neither.

Every origin forecasts the next one-hour interval from the preceding 168 hours.
Observed earlier validation/test readings may become history at a later origin.
This is rolling-origin forecasting, not an open-loop multi-day or zero-history
forecast. Train/validation/test target periods never overlap.

Targets are never filled. All five methods share the same eligible targets:
observed target and lags 1/24/168, with at least 80% observed history. Other past
gaps are causally forward-filled inside the window and marked with a binary
mask. No future/backward interpolation or full-series normalization is used.
Per-origin scale is past-window observed mean, floored at 1 kW. It is not fitted
from future hours or unseen buildings' full histories. Cohort exclusions are
recorded per building, including the entirely unavailable building.

## Network and fitting

The last 48 hours of scaled past load and observed mask enter a one-layer GRU
with hidden size 16. The 16 final hidden values join eight known inputs:
scaled lags 1/24/168, missing fraction, and target-hour/day-of-week sine/cosine.
A 24→16→1 head predicts a residual over the previous-week value. Outputs are
clamped nonnegative. No building identity embedding or unavailable feature is
used.

CPU PyTorch 2.13.0, Python 3.12.10; deterministic algorithms, one CPU thread,
seed 20261024. AdamW, learning rate .001, weight decay .001, batch 128,
SmoothL1 loss on history-scaled targets, gradient clip 1, maximum 100 epochs,
patience 12. Actual run: **77 epochs, best epoch 65**. The full measured loss
history and nonzero weight update are in the manifest.

Baselines: persistence, daily seasonal-naive, weekly seasonal-naive, and Ridge
with fixed alpha 10 on recent lags/masks/calendar; Ridge normalization fits only
train. The preferred method and neural stopping use validation macro-building
history-scaled MAE. No hyperparameter or threshold is selected on test results.
No comparison with the old 28-day cleaned-data baseline is presented as a gain.

## Actual held-out results

All errors below are kW. Each method uses exactly the same target cohort.

| Method | Test MAE | Test RMSE | Unseen-building MAE | Unseen-building RMSE |
|---|---:|---:|---:|---:|
| Weekly seasonal-naive | 6.9561 | 14.6237 | 1.9935 | 3.7072 |
| Daily seasonal-naive | 5.2098 | 13.5917 | 1.8871 | 3.8776 |
| **Persistence (preferred)** | **3.9336** | 8.8408 | **1.3528** | 3.4453 |
| Ridge | 4.1194 | 7.6019 | 1.5848 | 3.2637 |
| EnergyDNA GRU | 4.1866 | **7.4530** | 1.4413 | **2.9459** |

Training has 7,879 eligible targets. Test has 3,013 eligible targets from seven
previously trained buildings.
Generalization has 1,288 targets from three never-trained buildings, **including
432 zero-control targets**. Removing the constant-zero control gives
macro-building MAE **2.1688 kW GRU versus 2.0355 persistence** on the two
nonconstant unseen buildings. Thus the apparent lower aggregate generalization
MAE is not evidence of better generalization than the ordinary test buildings.
Both scales/building populations and the zero control differ.

Validation: 3,436 targets; history-scaled macro MAE persistence .108085,
GRU .115268, Ridge .115633, daily .170700, weekly .208681. The GRU therefore
fails the predefined criterion for replacing the preferred simple baseline.
Per-building MAE/RMSE and normalized errors are retained in both evaluation
reports. Errors are correlated over hours; no confidence interval or statistical
significance claim is made. This is one short seasonal sample and one fixed seed.

## Artifact, replay and verification

Checkpoint SHA-256:
`56d366ec3532a6e7267e819be86c7044e6c10b9505d163b9b395d222f3c2f5b6`.
Versioned under `research/energydna/artifacts/gru-v1/`: actual `model.pt`,
JSON Ridge parameters, manifest/training history, evaluation and independent
saved-artifact replay. Exact commands are in the [research README](../../research/energydna/README.md).
Three full training runs reproduced the same weight checksum (77 epochs, best
epoch 65); the final run took 138.3 seconds on the local CPU. Research
source fingerprint is
`3235b9d58d74471c31fa61a1c0524b32a99c0719e706735e39dce7ec5cc201b2`.
Versioned JSON artifacts are written with explicit LF bytes so their checksums
survive Git checkout on both Windows and Linux.
Replay reloads checksum-verified weights with `weights_only=True`, reconstructs
source-hashed windows and cohorts, and compares measured metrics with the saved
report without fitting any parameters. The loader also checks the research
source/feature/horizon identity. This is not a production signing registry.

Tests exercise future-data and held-out-building mutation, causal gaps, excluded
missing targets/weekly references, time and metadata rejection, actual tiny
training, deterministic checkpoint reproduction, reload and tamper rejection.
CI also infers from the committed actual BDG2-trained checkpoint, without a
network dataset download. Official engine/shared API/frontend files are intact.
