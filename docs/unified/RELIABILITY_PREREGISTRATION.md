# FragilityNet reliability comparison: protocol frozen before fresh holdout

The prior 900-row test and 1,800-row equipment generalization set have already
been inspected. They are **not pristine for new model-selection claims**.
Their 20 test false negatives will be explained by replay, not used as fitting
examples or threshold targets. No changes to the generator/physical equations.

Freeze this protocol in Git before generating the new holdout:

- Train/validation: original seed 20261024, 5,400/900 rows. No test gradients.
- New holdout: existing `ml_bridge.generate.generate_dataset`, seed **20261025**,
  count **6,000**; use only its `test` (600) and `generalization` (1,200) groups.
  Whole capacities remain disjoint from training/validation. Generated train/
  validation rows of that seed are discarded. Check input/signature uniqueness
  against every original row. New labels must be genuine unchanged official v1.
- Models: frozen registered logistic, frozen registered MLP; a validation-only
  threshold adjustment of frozen MLP; a 64/32 MLP with added input-only timing/
  energy/power features; a lightweight Ridge-style logistic on those same features.
- Fixed new MLP: seed 20261025, train-only StandardScaler, 64/32 ReLU, AdamW
  lr .002 / decay .001 / batch256, weighted BCE, max160epochs, patience20.
  Best validation BCE weights, validation temperature fit; one architecture/run.
- Threshold: maximize validation precision subject to recall >=.99 and precision
  >=.80 on the fixed .01..99 grid. If infeasible use validation F2 and explicitly
  report that the intended validation safety constraint was infeasible.
- Promotion gate (both fresh groups): dangerous recall >= frozen logistic and
  frozen MLP; precision >=.80; false-positive rate <= frozen MLP + .03;
  F1 >= frozen MLP - .02; Brier <= frozen MLP + .02. A failure on either group
  means **no automatic upgrade registration**. Physics remains authoritative.
- Report confusion/FN/recall/precision/F1/PR-AUC/Brier/ECE, power/islanding/PV/
  grid restoration subgroups, range OOD warnings and warm inference timings.
  Calibration is against synthetic labels only. No real-world outage probability.
- Examine all 20 original missed test scenarios: IDs, input hashes, first failed
  interval plus preceding trace, reserve/power/islanding/PV/grid and demand.
  Use trace-supported diagnostic flags, not an unverified unique causal story.
- Do not tune or rerun architectures after opening fresh holdout scores.

New features are explicit simplifying input summaries, never dispatch outputs:
time to first restoration; critical demand before restoration; available PV
during islanding; useful initial battery energy; integrated critical/requested
deficit; inverter/discharge shortfall; first-half/last-half supply; and maximum
islanded block energy deficit. Scheduled grid/PV inputs are scenario assumptions,
not forecasts of real future weather/grid events. They are not a second dispatch
engine and cannot mark an engineering outcome verified.
