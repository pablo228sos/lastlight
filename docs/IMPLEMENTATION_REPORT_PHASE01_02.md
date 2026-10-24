# LASTLIGHT Phase 01–02 implementation report

Date: 24 October 2026. Branch: `feat/physics-ml-foundation`.
[Draft PR #7](https://github.com/pablo228sos/lastlight/pull/7), related to Issues
#2 and #3. Base main: `dadf01d`. The existing team physics contribution
`776caa4` is included; its source branch and the cinematic branch are preserved.

## Implemented

- Independent deterministic Python dispatch with strict nested Pydantic inputs,
  variable critical/noncritical/PV/grid profiles, battery and inverter limits,
  efficiencies, islanding, shedding, exact within-step depletion and per-row /
  cumulative energy balance checks. The default input step is 15 minutes.
- The 24 kWh / 80% / 20% / 1.5 kW / 95% reference produces **9.12 hours**.
  Trace rows represent real event intervals; there is no fabricated initial
  powered row. Boundary failures at the exclusive horizon are censored.
- One authoritative wire schema; real OpenAPI and TypeScript types generated
  from it. The old overlapping frontend simulation contracts are removed.
- Reproducible Parquet generation, disjoint equipment-group splits, train-only
  feature normalization, logistic baseline, a real 27→64→32→1 PyTorch MLP,
  early stopping, validation calibration/threshold selection, checkpoint
  save/load, independent evaluation and deterministic inference.
- Deterministic physics frontiers, actual ML boundary proposals with independent
  physics verification, and equal-budget measured comparisons. The displayed
  map uses the exact physical method rather than an interpolated ML estimate.
- FastAPI simulation, comparison, prediction, frontier and working baseline
  demand-forecast endpoints. Every ML prediction includes authoritative physical
  summary/trace; out-of-domain and uncertain estimates require physics.
- School DISCONNECT GRID now requests a real run. SOC, instantaneous served
  critical demand, full-run unserved energy, observed first failure, timeline
  and lighting come from that one trace. Optional verified ML proposals appear
  on the frontier. Reset/site changes invalidate stale responses. Backend
  failure explicitly becomes rehearsal and removes calculated figures.
- Actual BDG2 download/preparation, missingness and time-policy checks,
  building/time holdouts, evaluated Cold Start and Historical baselines, and
  usable baseline forecast functions/API. **No neural EnergyDNA-Net is claimed.**

The existing world geometry, school coordinates, site identities, scene scale,
camera trajectories and assets are unchanged. A dry-run merge with the current
`feature/cinematic-integration` branch completed without conflicts. Main and
the other feature branches were not pushed to or rewritten.

## Architecture and tradeoffs

The existing `services/simulation` package is extended rather than replaced by
a duplicate `apps/api`. Physics has no ML or rendering dependency. ML labels
use the same engine that verifies predictions. Small versioned checkpoints
ship with their preprocessing; raw research data and Parquet remain ignored.

The API keeps original v1 wire names and fractional SOC; the additive contract
is 1.1. React has a dedicated visual adapter and performs formatting, not energy
dispatch. Physical frontier requests do not incur a cold Torch import; explicit
ML proposals are a separate action. A complete trace at one SoC proves all
shorter horizons for the same input prefix, so this simple exact approach is
the reference for the two-dimensional map.

## Dataset and measured model results

Generator seed `20261024`, physics `lastlight-dispatch-1.1.0`, feature contract
`input-statistics-1`. Dataset identity:
`499282b4754ee6eb88a3e342e5d8d93a8de5c17b244209a18f92a55a03c64e2d`.

6,000 synthetic physics-labelled scenarios: 3,600 train, 600 validation,
600 independent test and 1,200 generalization. Whole battery/inverter groups
are kept in one split; generalization uses unseen capacities/inverter levels.
Every row carries replay inputs, version, seed, outcome and provenance.
The initial 3,000-row validation experiment was compared before choosing the
larger dataset; final test data was not used for preprocessing or tuning.

Model **fragility-1-0e9fbf8a5ba1**: 63 training epochs, 18,365-byte checkpoint.
The final full training took 6.94 seconds after imports on the local CPU.

| Split / model | Accuracy | Precision | Dangerous recall | F1 | PR-AUC | ROC-AUC | Brier | ECE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Test logistic | .9000 | .9168 | .9681 | .9417 | .9927 | .9618 | .09420 | .12781 |
| Test FragilityNet | .9300 | .9258 | .9960 | .9596 | .9964 | .9822 | .04139 | .02727 |
| Generalization logistic | .8742 | .8749 | .9658 | .9181 | .9802 | .9464 | .12351 | .14569 |
| Generalization FragilityNet | .9008 | .8858 | .9920 | .9359 | .9928 | .9803 | .04987 | .01574 |

Test confusion matrices `[survives,fails]`: baseline `[[55,44],[16,485]]`,
MLP `[[59,40],[2,499]]`. Generalization: baseline `[[203,121],[30,846]]`,
MLP `[[212,112],[7,869]]`. FragilityNet improves this baseline but still misses
two dangerous test scenarios and seven generalization scenarios. The test
misses were physically re-run: a 2 kW inverter cannot serve a 2.0352 kW spike
despite available battery energy; a 6 kWh battery depletes at 7.59756 hours in
another profile. Full examples, thresholds and calibration are in the versioned
[evaluation](../ml/artifacts/fragility-v1/evaluation.json) and
[independent test report](../ml/artifacts/fragility-v1/independent-test.json).

These are synthetic-data results. They do not estimate real-world outage
probability or authorize equipment. See the [model card](MODEL_CARD_FRAGILITY.md).

## Actual frontier benchmark

Both cases use a 17×33 reference grid (561 independently simulated points).
The sampled methods get 80 physical calls and the same nearest-neighbour
reconstruction. ML includes feature extraction/inference and per-column
coverage planning in its measured time. The exact method uses 17 full traces.
Times below are individual warm CPU measurements, not deployment latency or
evidence of general speed across hardware. Model import/checkpoint I/O is
outside these timers. Error is mean discrete boundary displacement in hours.

| Case / method | Physics calls | Seconds | Boundary error h | Missed unsafe cells |
|---|---:|---:|---:|---:|
| Battery only / uniform | 80 | .0944 | .9168 | 10 |
| Battery only / random | 80 | .0823 | .9605 | 12 |
| Battery only / ML guided | 80 | .1551 | 2.1829 | 51 |
| Battery only / exact trace | 17 | .0383 | 0 | 0 |
| Variable profiles / uniform | 80 | .0890 | 1.3971 | 11 |
| Variable profiles / random | 80 | .0875 | 1.0915 | 13 |
| Variable profiles / ML guided | 80 | .1924 | 3.0997 | 36 |
| Variable profiles / exact trace | 17 | .0531 | 0 | 0 |

Dense reference construction took .6198 / .6433 seconds. **The tested ML-guided
strategy does not accelerate or improve this frontier.** The physical method
is used for the displayed result. This is a useful negative result, not evidence
that all ML sampling strategies are ineffective. Full data:
[frontier-benchmark.json](../ml/artifacts/fragility-v1/frontier-benchmark.json).

## EnergyDNA preparation: actual research subset

BDG2 commit `9b97ccbe90096aff42ed4fd6493bf7ae692d7118`, twelve overseas buildings,
first 672 hours of cleaned electricity: 8,064 building-hours, 2,058 missing
readings retained as missing, no nonmissing invalid values. Split: seven train,
two validation, three test buildings. An explicit local-standard-time policy
was used; timestamps are aligned to UTC and lags only use earlier observations.

Cold Start category/hour baseline: MAE **76.474 kW**, RMSE **78.477 kW** on
1,344 observed held-out rows. Historical previous-week baseline: MAE
**5.820 kW**, RMSE **11.425 kW** on 1,175 eligible chronological holdout rows.
The weak Cold Start result is reported as such. These forecasts are whole-
building research estimates, not measured Kyrgyzstan load or critical-load
forecasts. Source, attribution, transformation and limitations:
[DATA_PROVENANCE](DATA_PROVENANCE.md).

## Files created and modified

| Area | Main files |
|---|---|
| Physics | `services/simulation/{schemas,engine,__init__,fixtures}.py`, `docs/physics/*` |
| API | `services/simulation/{api,intelligence,forecast}.py` |
| Data | `ml/data/{generate_scenarios,download_bdg2_sample,prepare_bdg2}.py`, `ml/features.py` |
| Models/training | `ml/models/{fragility_net,energy_dna}.py`, `ml/training/train_fragility.py` |
| Evaluation | `ml/evaluation/{metrics,evaluate_fragility,benchmark_frontier}.py`, `ml/frontier.py` |
| Artifacts | `ml/artifacts/fragility-v1/*`, `ml/artifacts/energy-dna-baseline/profiles.json` |
| Frontend | `App.tsx`, mission state, generated contracts, simulation hook/adapter, PhysicsPanel, EvidenceDrawer, Vite proxy |
| Tests/tooling | `tests/simulation/*`, `tests/ml/*`, `scripts/generate_contracts.py`, Playwright physics tests/config, CI, requirements |
| Documentation/evidence | README, engineering/product/changelog, model/data/architecture/report docs, `evidence/phase-01/*` |

The [full changed-file manifest](PHASE01_02_CHANGED_FILES.txt) includes generated
schemas/fixtures and the inherited team contribution. No large dataset is
tracked. Visual proof: [phase-01 browser captures](../evidence/phase-01/README.md).

## Commands actually executed and outcomes

- Installed the service/test requirements plus pandas and PyArrow; reused the
  CPU Torch 2.13 installation, then pinned the actual scientific-library versions.
- `python -m pytest tests reference/legacy-physics -q`: **42 passed**, covering
  numerical/API/ML/forecast behaviour and the HTTP-description regression.
- `python -m ruff check ml scripts services/simulation tests`: passed.
- `python -m services.simulation.fixtures --check`: passed locally; cross-Python
  HTTP 422 description drift was identified on Linux and fixed explicitly.
- `python -m scripts.generate_contracts --check`: passed.
- `npm run build`, `npm run lint`: passed. The existing large-chunk warning remains.
- Existing and new browser tests: **6 passed, 1 intentional CI media skip**,
  including real school dispatch, first failure, verified ML proposals and
  unavailable backend. Linux software-WebGL tests are serialized to avoid CPU
  starvation of the original GSAP descent; its trajectory/timeout were not changed.
- Generated 3,000-row and 6,000-row Parquet datasets, trained/evaluated real models,
  reloaded checkpoints and independently evaluated held-out splits. Re-generated
  the final dataset to verify its identity.
- Downloaded/prepared the actual BDG2 subset and evaluated both baselines.
- Captured the production build at 1440×900 and 1920×1080 using local physics.

Local model-training environment: Python 3.13.15, Torch 2.13.0+cpu, NumPy 2.2.6,
SciPy 1.15.3, scikit-learn 1.6.1, pandas 3.1.0 and PyArrow 26.0.0. CI targets
Python 3.12 and Node 22. Exact floating-point results across library releases,
platforms and hardware are not promised; pinned environments, seeds, versions,
input hashes and deterministic inference are supplied for reproducibility.

Exact install, simulation, training, evaluation, API-start and frontend commands
are in [README](../README.md). Remote check results are linked on PR #7; they
are not inferred from local success.

## Known limitations and remaining research

- Simplified single-bus model: no AC transients, voltage/protection, equipment
  startup, degradation, measured local demand or regional field validation.
- Synthetic FragilityNet has compressed temporal features, discrete equipment
  assumptions and false negatives. Feature-range OOD and uncertainty flags are
  limited heuristics. Physics remains mandatory.
- The tested ML sampler is inferior to the exact frontier method. Advanced
  active learning and a broader benchmark are future research, not claimed gains.
- EnergyDNA is baseline inference/preparation, not a trained neural forecaster.
  Weather-conditioned training and NASA POWER/PVGIS ingestion are future work.
- Backend deployment, authentication for any future private data and real-site
  engineering verification are outside this local research milestone.
- Earlier visual-audit issues such as WebGL failure isolation, camera pause,
  modal focus trapping and narrow-screen hotspots are not broadly redesigned
  here; concurrent cinematic work is kept separate. The numerical integration
  does correct inconsistent outage controls when switching views/sites.

## Commit and review record

- `776caa4`: existing team's physical service and contract, preserved as ancestry.
- `198eee9`: validated variable-demand extension and explicit physics metadata.
- `3dcae36`: trained ML, evaluated baselines, verified frontier and forecast foundation.
- `72888d3`: school trace integration, generated TS types, UI/CI changes.
- `a95ce9d`: forecast regression-test correction.
- `0fff6f1`: explicit cross-Python HTTP error descriptions; strict artifact checks retained.
- `1ce3864`: sequential software-rendered CI checks and pinned training environment.

Later verification/documentation commits and the complete reviewable diff are
on [Draft PR #7](https://github.com/pablo228sos/lastlight/pull/7). No merge into
main is performed as part of this task.
