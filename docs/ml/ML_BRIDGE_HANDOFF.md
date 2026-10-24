# ML bridge handoff: Beksultan and Abai

This branch starts at release-candidate PR #13 `479e8d1`. It does not merge or
rewrite PR #7, PR #14, PR #13, main, or their shared Physics Engine files.

Contract coordination proposal for Beksultan:
https://github.com/pablo228sos/lastlight/issues/2#issuecomment-6387014859 .
The additive paths below are proposed, not claimed as accepted production routes.
No design-search endpoint or shared simulation route is edited.

## Beksultan: optional integration

The existing Physics API remains unchanged and fully usable without ML. After
contract review, a service owner may optionally mount the separate router:

```python
from ml_bridge.api import create_router
app.include_router(create_router())
```

For isolated local evaluation, run `python -m uvicorn ml_bridge.api:app --host 127.0.0.1 --port 8010`
using the ML environment.
This companion app exposes only the proposed ML endpoints and calls the official
simulator; it contains no second dispatch implementation.

- `POST /api/v1/ml/fragility/assess`: request is `{scenario: <official-v1 request>}`
  plus optional exact physics/schema/feature identities. Output has untouched
  official `physics`, separate `neural`, `physics_authoritative:true` and
  `engineering_clearance:false`.
- `POST /api/v1/ml/fragility/candidates`: same scenario plus unique sampled
  `{initial_soc,duration_hours}` points, at most1,600, and limit at most12. Points
  may be taken from the existing official map. Each returned candidate gets a
  separate official simulation and includes its run ID, hash and full summary.
  No colored map or boundary algorithm is replaced and no speedup is claimed.

Missing ML dependencies or checkpoints, incompatible versions, mismatched source,
normalizer/catalog drift or corrupted weights produce a warning/status. Physical
assessment remains available. Unknown1.1 request fields are rejected explicitly.
An incompatible physical runtime is not disguised as official v1.

Generated [OpenAPI](bridge.openapi.json) and [TypeScript](bridge.contracts.ts)
describe the new envelope. They do not overwrite the official generated artifacts.

## Abai: display contract

Use `physics.summary` and `physics.trace` for every engineering number and visual
state. Physical identity stays at `physics.model_version`, schema at
`physics.schema_version`, with unchanged run/hash/seed/provenance fields.

Only if `neural.status === 'available'`, show its `model_version`, predicted
failure, `synthetic_failure_score`, OOD/uncertainty flags and warnings under
**AI ESTIMATE**. Keep **PHYSICS-VERIFIED RESULT** separate. If they disagree,
physics wins. A score is not a real-world grid-outage probability. A missing
estimate should leave the physical result/map available.

Only returned independently verified candidate objects may receive checked
markers. Their count is neither model accuracy nor measured outage history.
The existing exact physical map is still preferred over the tested ML sampler.
No frontend, scene, camera, stylesheet or old UX contract is changed here.

## Research evidence and acceptance

Read [compatibility](OFFICIAL_V1_COMPATIBILITY.md), the
[model card](FRAGILITY_V1_MODEL_CARD.md), and versioned checkpoint/evaluation reports
under `ml_bridge/artifacts/`. Test recall is96.63% for neural versus96.96% logistic;
the20 versus18 false negatives must be disclosed along with the improved F1.

P0 requires independent replay, backend/inference tests and green CI before
EnergyDNA training. The user clarified that these technical checks satisfy the
transition gate; separate teammate approval is not claimed. Forecast research
will remain separate from physical profiles until a units/provenance adapter is
reviewed. Real building engineering approval remains outside this research bridge.
