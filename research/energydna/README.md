# EnergyDNA-Net bounded forecasting experiment

Real PyTorch GRU research on pinned BDG2 historical electricity. This package is
separate from the official simulator and the optional FragilityNet adapter.
Nothing mounts it into the application or inserts forecasts into physical traces.

Use Python 3.12 and the same pinned CPU runtime as `ml_bridge/requirements.txt`:

```powershell
python -m pip install --require-hashes -r services/simulation/requirements-dev.lock
python -m pip install torch==2.13.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r ml_bridge/requirements.txt
python -m research.energydna.download
python -m research.energydna.train
python -m research.energydna.evaluate
python -m research.energydna.inference --building Rat_assembly_Francine --target "2016-03-20 12:00:00"
python -m pytest tests/energydna -q
```

The default download is bounded to twelve fixed IDs and 2,160 hours (90 days),
not the full two-year dataset. The previous 672-hour cleaned subset established
only baselines. Its metrics are not comparable to this raw-data experiment.
Upstream cleanup uses whole-series anomaly detection and zero-gap filtering;
raw readings avoid importing those retrospective filters into split targets.
Raw meter faults remain a limitation. See [attribution](NOTICE.md) and the
[model card](../../docs/ml/ENERGYDNA_MODEL_CARD.md).

Forecast the **next one-hour** whole-building electricity interval, interpreted
as average kW from its hourly kWh reading. At each hourly origin, 168 prior hours
are available. The last 48 hours of scaled load and observed masks enter a
one-layer 16-unit GRU. Its head also receives lag 1/24/168, missing fraction,
and target hour/day calendar cycles, and learns a residual over last week's
value. There are no building-ID embeddings, future readings or weather features.

Building IDs are sorted and permuted with seed 20261024 into 7 train / 2
validation / 3 generalization IDs. Time boundaries are 60%/80% of the uniform
hourly index: first 54 days train, next 18 validation, final 18 test. Only the
seven training buildings before the first cutoff fit weights and Ridge scaling.
Validation combines later hours of those buildings and validation-only IDs.
The test reports later hours of training buildings separately from the final
period of the three never-trained generalization buildings. Context from earlier
held-out hours is allowed at successive rolling origins; this is not a 432-hour
open-loop forecast or a zero-history cold-start experiment.

No target is imputed. Every method uses the same observed target cohort with
observed lags 1/24/168 and at least 80% observed past context. Other past gaps
are forward-filled inside the window only, with a mask. Per-origin scale is
the mean of the observed past 168 hours, floored at 1 kW; it never uses the
target or the full building series. Zero readings are retained. The manifest
reports a fully missing building and a constant-zero control explicitly.

Baselines are previous hour (persistence), previous day, previous week
(seasonal-naive), and Ridge on historical lags/masks/calendar. Ridge uses
train-only StandardScaler and a fixed alpha of 10. Neural early stopping and
the preferred method use validation macro-building history-scaled MAE. The
preferred method is retained even if test rankings differ; no test tuning.
Reports include physical MAE/RMSE, every building, a nonconstant-building
sensitivity metric, cohort counts and exclusions. All values are measured,
not presentation placeholders.

Artifacts include actual trained `model.pt`, hash/source contract, explicit
architecture/training history, JSON Ridge coefficients, source manifest and
independent replay. Reload verifies weights, baseline and source fingerprints
and uses `torch.load(weights_only=True)`. This is a research integrity check,
not a signed production model registry. Full training is local/reproducible;
CI runs leakage/missingness tests, tiny real training and committed artifact
inference without downloading BDG2.
