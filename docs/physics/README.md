# LASTLIGHT physics service

Start here for local setup; see [CONTRACT.md](CONTRACT.md) for integration and
[MODEL.md](MODEL.md) for equations, topology and limitations. This backend
requires no cloud service, account, ML weights or network connection to run.

## Windows: one command

Install Python 3.12 with the Python launcher, open PowerShell or Command Prompt
in the repository root, then run:

```powershell
.\services\simulation\start.cmd
```

The launcher creates an isolated environment, installs the hash-locked runtime
requirements once and starts on `http://127.0.0.1:8000`. Subsequent starts reuse
it; no shell activation or PowerShell execution-policy change is required.
Ctrl+C stops the server. Python 3.12 is the verified runtime. If the `py`
launcher is unavailable, use `python services\simulation\run.py` with a
Python 3.12+ interpreter. A custom port is supported: `start.cmd --port 8001`.

Swagger is at `http://127.0.0.1:8000/docs`. Its UI assets use a CDN, so the
interactive docs page needs internet. The API and `/openapi.json` are fully
local; the same OpenAPI schema is checked in at `docs/physics/openapi.json`.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
$body = Get-Content docs/physics/fixtures/baseline.request.json -Raw
$result = Invoke-RestMethod http://127.0.0.1:8000/api/v1/simulations -Method Post -ContentType application/json -Body $body
$result.summary
$result.trace
Invoke-RestMethod http://127.0.0.1:8000/api/v1/comparisons -Method Post -ContentType application/json -Body '{"upgrade":"full_precharge"}'
```

With an existing Python environment instead of the bootstrap:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r services/simulation/requirements-dev.lock
.\.venv\Scripts\python.exe -m uvicorn services.simulation.api:app --host 127.0.0.1 --port 8000
```

## Linux / macOS

```sh
python3.12 services/simulation/run.py
```

Or create a virtual environment and install the same requirements lock, then
run Uvicorn directly from repository root. `requirements.txt` and
`requirements-dev.txt` are direct dependency specifications; the corresponding
`.lock` files pin transitive dependencies with SHA-256 hashes across platforms.

## Fully offline demo

No Python or server is needed to inspect `fixtures/baseline.result.json`,
`fixtures/comparison.result.json` or `fixtures/regression-16h.json` under this
directory. These full synthetic traces are the UI fallback. Do not recreate
numbers in JavaScript or relabel them as measured data.

After the initial environment setup, disconnect the network and run:

```powershell
.\services\simulation\start.cmd --offline
```

For first-time setup on a disconnected Windows computer, download wheels on
an internet-connected **Windows computer with the same Python version and
architecture**, then transfer the wheel directory and repository:

```powershell
py -3.12 -m pip download --require-hashes -r services/simulation/requirements.lock -d wheelhouse
.\services\simulation\start.cmd --offline --wheelhouse .\wheelhouse
```

Keep wheelhouse and environments out of commits. You can also calculate and
print the entire trace without any HTTP server (use the environment's Python):

```sh
python -m services.simulation simulate docs/physics/fixtures/baseline.request.json
python -m services.simulation compare docs/physics/fixtures/comparison.request.json
```

Input is UTF-8 JSON (a UTF-8 BOM from Windows editors is supported). Omit the
filename for the reproducible baseline/default comparison. Invalid CLI input
exits with code 2 and an error on stderr.

## Verification and CI proposal

Install development dependencies, then run from repository root:

```sh
python -m pip install --require-hashes -r services/simulation/requirements-dev.lock
python -m services.simulation.check
```

This runs lint, formatting, frozen-fixture drift checks and the complete
Pytest/property/API suite with at least 95% engine/schema/API coverage. The
suite includes the 9.12/13.68/12.16 regressions, independent legacy comparisons,
SOC and power bounds, event timing, profiles, islanding, missing PV,
noncritical priority, both efficiency losses, conservation, reproducibility,
parallel calls, invalid input, JSON error contracts and local-only CORS.

Existing web checks remain separate:

```sh
npm ci --prefix apps/web
npm run build
npm run lint
CI=true npm run test:smoke
```

The browser command above uses POSIX environment syntax; on PowerShell use
`$env:CI = 'true'` before `npm run test:smoke`. Install Chromium as described by
the existing workflow when running the CI browser suite locally.

Issue #2 owns only `services/simulation/**`, `tests/simulation/**` and
`docs/physics/**`. Therefore the proposed Python workflow is included as
[simulation-ci.yml](simulation-ci.yml) here. The repository's workflow owner
should copy it to `.github/workflows/simulation.yml` to enable automatic
Windows/Linux checks; this PR does not silently modify an unowned path.

Frozen JSON contracts are generated from Pydantic and the actual API:

```sh
python -m services.simulation.fixtures
python -m services.simulation.fixtures --check
```

Regenerate intentionally when changing a contract and review the diff. Proposed
additions for the web owner are in [contracts.proposed.ts](contracts.proposed.ts).
