# Independent official-v1 compatibility report

Source of truth: release-candidate PR #13, commit
`479e8d1fdbb0c357f61468c8934a314f345a15ed`. Official versions remain
`lastlight-dispatch-1.0.0` and schema `1.0.0`. No official runtime file was changed.

## Decision: retrain, do not relabel the old checkpoint

The unmodified PR #7 model `fragility-1-0e9fbf8a5ba1` was loaded in its original
1.1 research runtime. Its original manifest and weights were not rewritten.
The audit used the actual 6,000-row research Parquet and official-v1 validation:

- **6,000 / 6,000 requests are rejected** as official v1 requests because every
  generated request includes critical/noncritical load-profile fields that v1
  does not define. V1 accepts constant critical/noncritical demand; its PV and
  grid-availability profiles remain supported.
- **1,819 rows** have constant load profiles and can be explicitly projected to
  scalar loads. All those projected outcome labels agree with official v1. This
  restricted overlap does not validate variable-load inputs or the whole model.
- The original feature extractor accesses 1.1-only load fields and does not
  encode all official grid controls. Its normalizer and calibration were fitted
  on a different distribution. Renaming its version would bypass a meaningful
  guard rather than demonstrate compatibility.
- Independent replay reproduces a label disagreement at the exact exclusive
  **9.12-hour** endpoint: the original 1.1 engine reports failure at steps 1 and
  15 minutes; official v1 correctly reports no observed failure in `[0,9.12)`.
  Both report failure after that boundary. The 60-minute exact case agrees.

The complete machine report, including restricted-overlap model metrics, is
[legacy-compatibility.json](../../ml_bridge/artifacts/legacy-compatibility.json).
Its restricted metrics are not a production accuracy claim. The old 93% result
is not carried forward to the new checkpoint.

## Independent new evidence

New data is generated only through the unchanged official `SimulationRequest`
and `simulate`. New features, normalization and weights have a new identity.
All **9,000** generated requests, input hashes, outcome summaries and input-only
feature vectors were independently replayed before artifact registration.
The new [model card](FRAGILITY_V1_MODEL_CARD.md) reports the actual held-out scores,
including false negatives and a baseline tradeoff.

The bridge checks exact physics/schema identities, canonical official source and
request-schema hashes, feature order/version/source, normalization dimensions,
finite parameters, checkpoint checksum and an independently validated artifact
catalog. The catalog pins the complete canonical preprocessing manifest as well
as the weights, so changing only normalizer values is rejected too.

The physical result remains nested and unmodified under `physics`. Neural model
identity is under `neural.model_version`; it never replaces the physical model's
identity. Missing or mismatched ML leaves the physical calculation available.
Unsupported 1.1 request fields are rejected, not silently averaged or discarded.

## Reproduce

From a checkout of this branch with the documented ML environment:

```sh
python -m ml_bridge.audit_legacy --legacy-root /path/to/pr7-checkout --legacy-data /path/to/pr7-checkout/ml/data/generated/scenarios.parquet
python -m ml_bridge.generate --count 9000 --seed 20261024
python -m ml_bridge.train --seed 20261024
python -m ml_bridge.evaluate --register
```

The old checkout/data paths are required only for the old-versus-official audit.
The new production adapter never imports the old package or invokes its engine.
