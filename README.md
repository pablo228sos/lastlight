# LASTLIGHT

An interactive energy resilience digital twin by CURSED, Kyrgyzstan.

LASTLIGHT explores how a building's local energy system might respond when the grid goes down. The current release is a cinematic, interactive prototype for the LOGOS Hackathon 2026 final.

![School inspection in the night district](evidence/phase-00.5/facility-1920x1080.png)

## Experience

Fly into a synthetic night district, select the school, inspect its solar panels, inverter and battery, disconnect the grid, then reset the scene. The camera stays inside one modeled world throughout the journey. Lighting and the visible power path respond to the outage control.

The school outage now runs a deterministic single-bus energy calculation and displays its trace. Inputs and district geometry remain synthetic; there is no measured school meter data or live utility connection. If the service is unavailable, the interface explicitly falls back to a visual rehearsal without calculated figures.

## Run locally

Use Node.js 22 and Python 3.12 (also verified locally on Python 3.13).

From the repository root, create and activate a virtual environment, then install:

```sh
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install torch==2.13.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements-ml.txt
python -m uvicorn services.simulation.api:app --host 127.0.0.1 --port 8000
```

In another activated terminal, start the existing web app:

```sh
cd apps/web
npm ci
npm run dev
```

Open the address printed by Vite. Its `/api` proxy points to the local service;
set `LASTLIGHT_API_URL` for another backend. Select School, disconnect the grid,
inspect the trace or jump to the first failure, then open Failure Frontier.
The physical map loads first; **Verify ML proposals** adds real FragilityNet
proposals checked by the simulator. They do not grant engineering clearance.

## Verify

From the repository root:

```sh
npm run build
npm run lint
npm run test:smoke
```

The Python environment must be active for browser tests; Playwright starts the
local API as well as Vite. Install its Chromium with `cd apps/web` then
`npx playwright install chromium`. For local Chrome-based media capture install
Chrome; `CI=true` uses the bundled Chromium and skips only media recording.

```sh
python -m pytest tests reference/legacy-physics -q
python -m ruff check ml scripts services/simulation tests
python -m services.simulation.fixtures --check
python -m scripts.generate_contracts --check
```

## Reproduce physics and ML

The checked-in small checkpoint is already trained. Full experiments are separate
from CI; raw data and Parquet datasets are ignored by Git.

```sh
python -c "from services.simulation.schemas import SimulationRequest; from services.simulation.engine import simulate; print(simulate(SimulationRequest()).model_dump_json(indent=2))"
python -m ml.data.generate_scenarios --count 6000
python -m ml.training.train_fragility --epochs 240
python -m ml.evaluation.evaluate_fragility
python -m ml.evaluation.benchmark_frontier
python -m ml.data.download_bdg2_sample
python -m ml.data.prepare_bdg2 --meters ml/data/raw/bdg2/electricity-sample.csv --metadata ml/data/raw/bdg2/metadata.csv --timestamp-mode local_standard
```

Run a simulation with `POST /api/v1/simulations` and JSON `{}`; the observed
baseline failure is 9.12 hours. `/docs` and `/openapi.json` describe prediction,
frontier, comparison and baseline demand-forecast endpoints. See the
[architecture](docs/ML_ARCHITECTURE.md), [model card](docs/MODEL_CARD_FRAGILITY.md),
[data provenance](docs/DATA_PROVENANCE.md) and [implementation report](docs/IMPLEMENTATION_REPORT_PHASE01_02.md)
for actual results and limitations.

The browser suite covers the camera journey, facility selection, view layers, outage, reset, reduced motion and projector resolution. Local runs also capture screenshots and video. GitHub Actions checks interactions with Chromium and runs the separate physics reference tests without recapturing media.

See the [visual review](evidence/phase-00.5/README.md), [1440 x 900 opening](evidence/phase-00.5/opening.png), [1920 x 1080 outage](evidence/phase-00.5/offline-1920x1080.png) and [recorded interaction](evidence/phase-00.5/interaction-demo.webm).

## Repository

- `apps/web`: React, TypeScript, Vite and React Three Fiber application.
- `apps/web/tests`: Playwright browser checks.
- `docs/PRODUCT.md`: audience, experience and current claims.
- `docs/ENGINEERING.md`: the physics contract and a reference calculation.
- `evidence/phase-00.5`: actual browser screenshots, video and review notes.
- `reference/legacy-physics`: archived energy balance research and unit tests, not part of the running app.

School figures and physical lighting now use one simulation trace. FragilityNet
has been trained on synthetic physics labels and compared with logistic
regression. Exact physical frontier construction outperformed the tested
ML-guided sampling strategy. Demand forecasting has working research baselines;
a neural EnergyDNA-Net and regional validation remain future work. See the
[change log](CHANGELOG.md) for the project's development path.

Team contributions follow the [branch and review workflow](CONTRIBUTING.md). Work items and progress belong in GitHub Issues and pull requests.
