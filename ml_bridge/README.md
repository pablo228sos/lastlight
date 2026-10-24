# Optional official-v1 ML bridge

This package imports the unchanged release-candidate Physics Engine. It keeps
the neural estimate separate from the authoritative physical response. It does
not replace shared routes or the frontend.

## Install and verify (Python 3.12)

```sh
python3.12 -m venv .venv
# Activate .venv using the platform's standard command.
python -m pip install --require-hashes -r services/simulation/requirements-dev.lock
python -m pytest tests/ml_bridge/test_bridge.py -q
python -m pip install torch==2.13.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r ml_bridge/requirements.txt
python -m services.simulation.check
python -m pytest tests/ml_bridge -q
python -m ml_bridge.export_contract --check
```

On Windows, create the environment with `py -3.12 -m venv .venv` and use
`.venv\Scripts\python.exe` for the commands. Exact pins are supplied; training
environment details are also saved in the artifact manifest.

## Reproduce the research checkpoint

```sh
python -m ml_bridge.generate --count 9000 --seed 20261024
python -m ml_bridge.train --seed 20261024
python -m ml_bridge.evaluate --register
```

Generation stores ignored Parquet; training fits a logistic baseline
and actual PyTorch MLP using train-only normalization, validation selection and
disjoint capacity groups. Evaluation replays all labels/features with official
physics before registering the proposed artifact. Review catalog changes before
shipping a new model. No old checkpoint version is renamed.

## Run the proposed companion API

```sh
python -m uvicorn ml_bridge.api:app --host 127.0.0.1 --port 8010
```

This is an isolated research app. Production mounting/path acceptance belongs to
the official service owner; shared files remain unchanged. All physical analysis
works without the optional neural dependencies. Neural inference never grants
engineering approval. See [handoff](../docs/ml/ML_BRIDGE_HANDOFF.md),
[compatibility](../docs/ml/OFFICIAL_V1_COMPATIBILITY.md), and
[model card](../docs/ml/FRAGILITY_V1_MODEL_CARD.md).
