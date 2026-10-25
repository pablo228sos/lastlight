# Run and review unified LASTLIGHT

Review base: PR19 `feat/official-v1-ml-bridge` at `b3b4c4b`, which is stacked on
release-candidate PR13 `479e8d1`. Work branch: `feat/unified-ml-intelligence`,
[Draft PR21](https://github.com/pablo228sos/lastlight/pull/21),
[Issue20](https://github.com/pablo228sos/lastlight/issues/20).
No main push/merge, teammate-branch rewrite or imported legacy 1.1 physics.

## Windows local launch

Python **3.12**, Node **22+**. From the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r services/simulation/requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install torch==2.13.0 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r ml_bridge/requirements.txt
.\.venv\Scripts\python.exe -m uvicorn services.simulation.api:app --host 127.0.0.1 --port 8000
```

In a second terminal, from `apps/web`:

```powershell
npm ci
npm run dev -- --host 127.0.0.1 --port 4173
```

Open <http://127.0.0.1:4173>. Vite proxies `/api/v1` to the single official API.
If another local server uses that port, Vite reports its chosen free port. Do not
silently use another checkout's page or API for validation. Existing standalone
physics launchers/dependency locks continue to work without neural packages.
No BDG2 download is needed for the packaged one-hour UI examples.

Select School → Disconnect Grid → Run AI Resilience Analysis. The optional
16-hour action is an actual new official request. Failure Frontier uses the
active capacity/window; AI suggestions add separate independently checked
markers. Demand Research is a distinct historical one-hour preview.

## Actual API and identity behavior

- `POST /api/v1/simulations`, `/comparisons`, `/frontiers`: existing physics.
- `POST /api/v1/ml/fragility/assess`: `{scenario:<official input>}` defaults to
  original registered PR19 v1 features. Add
  `feature_schema:"lastlight-official-v1-features-2"` for the timing model used
  by the website. `physics` and `neural` stay separate. No silent conversion.
- `POST /api/v1/ml/fragility/candidates`: same feature/scenario contract plus
  up to1,600 unique supplied map points and limit1–12. Each returned object
  includes its independently simulated physical summary/run/hash.
- `POST /api/v1/ml/energydna/forecast`: `{example_id:"rat-march20"}`; alternatives
  `silvia-march20`, `mouse-march20`. Real one-hour GRU plus persistence, observed
  history/actual, model identity, units, source/checksums/attribution.
- `GET /api/v1/intelligence/openapi.json`: complete additive actual contract,
  generated into `docs/unified/openapi.json` and web TypeScript. The original
  `/openapi.json` stays the exact frozen physical contract so the standalone
  physics installer and its fixtures remain unchanged.

To verify real missing-checkpoint fallback, launch a second API on8002 with
`LASTLIGHT_FRAGILITY_CHECKPOINT` and `LASTLIGHT_ENERGYDNA_CHECKPOINT` set to a
nonexistent directory. The timing route inherits that override, or can use its
own `LASTLIGHT_FRAGILITY_TIMING_CHECKPOINT`. Corrupt/mismatched artifacts are
also tested. Physical results remain available. Changed checkpoint bytes
invalidate warm cache; a failed neural estimate cannot authorize equipment.

## Verification

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m services.simulation.check
.\.venv\Scripts\python.exe -m pytest tests/ml_bridge tests/energydna -q
.\.venv\Scripts\python.exe -m ml_bridge.export_contract --check
.\.venv\Scripts\python.exe -m ml_bridge.export_unified --check
.\.venv\Scripts\python.exe -m ruff check ml_bridge research/reliability research/energydna tests/ml_bridge tests/energydna
```

In `apps/web`, with the genuine APIs running:

```powershell
npm run build
npm run lint
$env:LASTLIGHT_LIVE_API='1'
$env:LASTLIGHT_FALLBACK_API='http://127.0.0.1:8002'
$env:LASTLIGHT_WEB_URL='http://127.0.0.1:4173'
npm run test:smoke
```

The new browser test uses real successful HTTP responses, not mocked inference.
Its fallback test forwards requests to the actual second missing-model backend.
Set `LASTLIGHT_CAPTURE=1` to capture the connected screens at1366×768,1440×900
and1920×1080 under `evidence/unified/`. Two existing video-recording tests are
deliberately skipped under `CI=true`; camera/lighting/physics/browser checks run.

## Research reproduction

```powershell
python -m ml_bridge.generate --count 9000 --seed 20261024
python -m research.reliability.prepare
python -m research.reliability.compare
python -m research.reliability.register
python -m research.reliability.benchmark
python -m research.energydna.download
python -m research.energydna.package_examples
python -m research.energydna.evaluate
python -m research.energydna.multihour
python -m research.reliability.report
python -m ml_bridge.benchmark
```

Do not regenerate/inspect new test splits and then tune against them. The
protocol and source identities are fixed; changing them creates another
experiment with new holdouts. Original one-hour retraining is documented in
`research/energydna/README.md`. Raw Parquet/meter downloads stay ignored; small
weights, manifests, exact evaluations and attributed examples are versioned.

See [judge overview](OVERVIEW.md), [reliability](RELIABILITY.md),
[forecast evidence](FORECAST_EVIDENCE.md), [allocation boundary](FORECAST_TO_PHYSICS.md),
[latency](PERFORMANCE.md) and [presentation script](DEMO_SCRIPT.md). The model
cards in `docs/ml/` retain the earlier PR19 findings and point to this newer,
separately identified evidence.
