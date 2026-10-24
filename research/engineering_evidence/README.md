# Reproduce the engineering evidence

Research-only scripts. No copied production implementation, changed equations,
trained model, frontend edits or service endpoint. All scenario values are
synthetic. The plotting script reads saved engine observations; it does not
calculate physics. Source dates and limits are in
[`docs/research/SOURCES.md`](../../docs/research/SOURCES.md).

## Linux / macOS command syntax

The executions recorded for this research were on **Linux, Python 3.12.14**.
The following sibling-directory layout makes the command stored in every CSV
row directly executable. macOS and Windows execution of the research scripts
has not been independently verified here.

```bash
git clone --branch research/engineering-evidence https://github.com/pablo228sos/lastlight.git lastlight-evidence
git clone --branch feature/physics-api https://github.com/pablo228sos/lastlight.git lastlight-physics
git -C lastlight-physics checkout ef23a710ecb7b235ea734171730a4656c40f4615
python3.12 lastlight-physics/services/simulation/run.py --setup-only
cd lastlight-evidence
../lastlight-physics/services/simulation/.venv/bin/python research/engineering_evidence/run_sensitivity.py --engine-root ../lastlight-physics --check
```

`run.py --setup-only` installs/verifies the official hash-locked service
environment without starting HTTP. It needs package access for first setup;
after setup the research calculation is offline. `engine_pin.json` verifies
engine/schema/initialisation/requirements file SHA-256, Python 3.12 and Pydantic
2.14.1. A newer physics branch head is not silently accepted.

To regenerate the CSV/manifest instead of checking:

```bash
../lastlight-physics/services/simulation/.venv/bin/python research/engineering_evidence/run_sensitivity.py --engine-root ../lastlight-physics
```

To emit a full result trace for one row without changing files:

```bash
../lastlight-physics/services/simulation/.venv/bin/python research/engineering_evidence/run_sensitivity.py --engine-root ../lastlight-physics --case-id c24-soc80-p1.5-h12-m15
../lastlight-physics/services/simulation/.venv/bin/python research/engineering_evidence/run_sensitivity.py --engine-root ../lastlight-physics --case-id c36-soc80-p1.5-h12-m15
../lastlight-physics/services/simulation/.venv/bin/python research/engineering_evidence/run_sensitivity.py --engine-root ../lastlight-physics --case-id c36-soc80-p1.5-h32-m15
```

The first two results observe 9.12 h and null respectively. The third observes
13.68 h in a separate 32-hour window. `null` means no observed failure within
the selected window. The CSV's `input_json` holds the complete resolved request,
including defaults, UTC start, seed and provenance, not only varied columns.

## Audit published repository evidence

This checks the arithmetic of PR7's published confusion matrices, records its
published negative frontier comparison, compares both PR8 fixture files to PR6
byte-for-byte, and reproduces PR7's exclusive-horizon edge case in a temporary
process. It does **not** train/evaluate a new model or rerun benchmark timing.

```bash
git -C ../lastlight-physics fetch origin refs/pull/7/head refs/pull/8/head
../lastlight-physics/services/simulation/.venv/bin/python research/engineering_evidence/audit_repository_evidence.py --repository ../lastlight-physics --check
```

Omit `--check` to regenerate `repository_evidence_audit.json`. Commits are pinned
inside the script, so repository evidence does not drift when a PR moves.
The clone must contain those commit objects; fetch does not modify any branch.

## Plot in a separate research environment

Do not add plotting packages to the production service lock/environment.

```bash
python3.12 -m venv research/engineering_evidence/.venv-plot
research/engineering_evidence/.venv-plot/bin/python -m pip install -r research/engineering_evidence/requirements-plot.txt
research/engineering_evidence/.venv-plot/bin/python research/engineering_evidence/plot_sensitivity.py
```

Verified plotting packages: Matplotlib 3.10.8 and NumPy 2.3.5. PNG and SVG are
under `docs/research/figures/`. Numeric data and labels are reproducible;
different font/rendering dependency versions can change image bytes.

## Windows syntax, not a Windows execution claim

With the same two sibling clones and Python 3.12 installed:

```powershell
py -3.12 ..\lastlight-physics\services\simulation\run.py --setup-only
..\lastlight-physics\services\simulation\.venv\Scripts\python.exe research\engineering_evidence\run_sensitivity.py --engine-root ..\lastlight-physics --check
..\lastlight-physics\services\simulation\.venv\Scripts\python.exe research\engineering_evidence\audit_repository_evidence.py --repository ..\lastlight-physics --check
```

The CSV stores a POSIX command; use this executable/path substitution on Windows.
Native Windows CI and presentation-machine acceptance remain separate checks
owned by the integration team. No research output upgrades their status.

## Recorded validation

- 75 deterministic results: 24 study rows, 48 time-step checks, 3 exact-horizon
  checks; all independent constant-load, UTC, SOC and energy checks passed.
- `--check` reproduced the saved CSV/manifest and repository audit.
- Published test/generalization confusion-matrix arithmetic matched; no ML
  acceleration claim is supported by the two recorded frontier benchmarks.
- Two frontend replay fixtures are byte-identical to the official backend's.
- Ruff checks passed on the isolated scripts; PNG was visually inspected.

The new evidence is scenario arithmetic and source/artifact inspection.
It does not constitute field validation, a new production CI run, or market
validation. Detailed numerical results:
[`SENSITIVITY_STUDY.md`](../../docs/research/SENSITIVITY_STUDY.md).
