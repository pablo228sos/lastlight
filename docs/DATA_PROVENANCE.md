# Data provenance and reproducibility

## FragilityNet: synthetic physics labels

No measured outage data is used. Generator seed is `20261024`; labels come from
`lastlight-dispatch-1.1.0`. Every row includes scenario/equipment IDs, resolved
parameters, seed, physics/generator/feature versions, input hash, physical-input
signature, feature vector, first failure if observed, unserved critical kWh,
survival label, summary and synthetic provenance. Datasets are Parquet and are
ignored by Git. Small checkpoints, preprocessing metadata and reports are
explicitly versioned.

| Parameter | Generator distribution |
|---|---|
| Base battery capacities | 6, 12, 18, 24, 36, 48 kWh |
| Unseen generalization capacities | 30, 42, 60 kWh |
| Base inverter limits | 2, 4, 6, 8, 12 kW |
| Generalization inverter limits | 3, 7, 11 kW |
| Initial/minimum/maximum SOC | uniform [0.3,1), minimum in {0.1,0.2,0.25}, maximum 1 |
| Efficiencies | independent uniform [0.88,0.98) |
| Charge/discharge limits | 0.75 × inverter / 1 × inverter |
| Critical/noncritical base load | uniform [0.4,6) / [0,5) kW |
| Load profile | 30% constant; otherwise a bounded daily sinusoid and one bounded spike |
| Solar capacity | {0,2,5,10} kW; synthetic 07–18 daylight, multiplier {0.3,0.65,1} |
| Horizon / starting UTC hour | {4,8,12,16,24} hours / integers 0..23 |
| Shedding / inverter islanding / PV islanding | 70% / 95% / 90% enabled |

All combinations satisfy the schema and storage-order constraints; non-islanding
equipment is a valid configuration that can fail, not an impossible sample.
These profiles do not represent Bishkek weather, actual school demand or
electrical startup behaviour. Correlated critical/noncritical profile shapes
and discrete equipment choices are important synthetic-data limitations.

The final 6,000 rows split into 3,600 train, 600 validation, 600 test and 1,200
unseen-equipment generalization rows. Whole capacity/inverter combinations are
assigned to a single split; physical signatures are unique. Generalization
uses capacities and inverter levels absent from the other pools. Normalization
is fitted on train only. Evaluation reports contain the actual distribution,
equipment memberships and feature ranges. Replay hashes identify the dataset.

The first 3,000-row experiment gave validation accuracy 0.9267, F1 0.9565 and
Brier 0.05279. Increasing to 6,000 improved validation accuracy to 0.9417,
F1 to 0.9654 and Brier to 0.04177. Dataset size was chosen from this validation
comparison, not test-set tuning. This establishes a reproducible first model;
it does not prove sufficient coverage for real equipment. The final test and
generalization results are reported separately in the model card.

## EnergyDNA research source

Primary source: [Building Data Genome 2](https://github.com/buds-lab/building-data-genome-project-2),
pinned commit `9b97ccbe90096aff42ed4fd6493bf7ae692d7118`.
Credit: Clayton Miller, Anjukan Kathirgamanathan, Balaji Picchetti and the BDG2
authors, *The Building Data Genome Project 2* (2020). The upstream repository
provides an [Attribution-ShareAlike 4.0 license](https://github.com/buds-lab/building-data-genome-project-2/blob/9b97ccbe90096aff42ed4fd6493bf7ae692d7118/LICENSE).
The derived `ml/artifacts/energy-dna-baseline/profiles.json` is distributed under
those same Attribution-ShareAlike terms, with this attribution and the explicit
modification notice: hourly category/global means fitted on the selected training
buildings. No endorsement by the dataset authors is implied.
The [dataset paper](https://www.nature.com/articles/s41597-020-00712-x)
documents hourly meter energy sums and local timestamps. These are overseas
research buildings, not measurements of buildings in Kyrgyzstan.

The bounded downloader resolves Git LFS content and selects twelve evenly
spaced electricity columns from the first 672 hours of
`data/meters/cleaned/electricity_cleaned.csv`. It saves source identity, selected
IDs and the SHA-256 of the local subset; raw data remains ignored by Git.
Metadata is joined by building_id, not column position. Preparation accepts
only explicitly declared hourly electricity kWh and converts to average kW.

Observed subset: 8,064 building-hours, 2,058 missing readings, zero negative or
nonfinite nonmissing readings. Missing targets are retained as missing, never
filled using future values. Hourly gaps are explicit; lag-24/lag-168 features
use previous hours after reindexing. Buildings are split 7/2/3 for
train/validation/test. No building appears in multiple groups.

Timestamp basis is mandatory: UTC, local standard time or local wall clock.
The measured subset used an explicit local-standard-time interpretation.
Ambiguous/nonexistent wall-clock hours are flagged; they are never guessed.
Timestamp interpretation must be reviewed for each new export, especially DST
and weather joins. The UTC timestamps, local clock features and source policy
are preserved. Baseline reports use building holdout for Cold Start and the
last chronological 20% for Historical, with previous-week observations.

The actual subset baseline scores are MAE 76.474 kW / RMSE 78.477 kW for Cold
Start (1,344 observed held-out rows), and MAE 5.820 kW / RMSE 11.425 kW for
Historical (1,175 eligible rows). These are weak research baselines across
different building scales. They do not validate forecasts for Kyrgyzstan or
critical loads. The versioned cold-start profile is fitted only on training
buildings; the neural EnergyDNA-Net has not been trained.

[NASA POWER](https://power.larc.nasa.gov/) and
[PVGIS](https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis_en)
remain additional climate-source candidates. No observations from either
service are claimed in these results. Weather-conditioned forecasting needs
an explicitly aligned source, missingness/provenance checks and separate
evaluation. Observed future weather must not be confused with an available
forecast at inference time.
