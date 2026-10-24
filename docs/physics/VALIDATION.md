# Validation record

Verified 24 October 2026 on Linux x86-64, Python 3.12.14, with the checked-in
hash-locked dependencies installed into a fresh isolated environment.

| Check | Result |
| --- | --- |
| `python -m services.simulation.check` | 124 passed, 0 failed; lint, formatting and 12 frozen contract/fixture files verified |
| Coverage: engine, schemas and API | 99.44% statements; 100% schemas and API |
| Constant-input regressions, steps 1/15/60 minutes | 9.12 / 13.68 / 12.16 hours |
| Independent archived-equation comparisons | 8 matching cases, including different capacity, efficiency and load |
| Generated invariant scenarios | 100 energy/equipment/profile cases plus 40 capacity-monotonicity pairs |
| Seven-day run at one-minute sampling | 10,080 contiguous rows; correct exclusive UTC horizon |
| Actual Uvicorn HTTP server, launched with `run.py --offline` | 20 recorded integration checks pass, including both launch/restart HTTP passes |
| Live HTTP baseline vs API fixture | Exact JSON equality; all 49 intervals included |
| Fresh first-time offline setup | Passed with `--offline --wheelhouse ... --setup-only`; pip used local wheels with hashes and `--no-index` |
| Offline CLI | Full baseline and comparison JSON equal to the API fixtures; Windows UTF-8 BOM supported |
| Proposed frontend TypeScript | Compiles with `tsc --strict --noEmit --skipLibCheck`; extends existing result interfaces |
| Existing local web checks | `npm ci`, build and lint passed |
| Existing GitHub Actions on first working increment | Web build/lint/Playwright and archived physics tests passed in [Verify run 4](https://github.com/pablo228sos/lastlight/actions/runs/40080649370) |

Phase 02 evidence is retained in [evidence/phase02/](evidence/phase02/):
[official check log](evidence/phase02/check.linux.log),
[integration report](evidence/phase02/integration.linux.json),
[first HTTP server log](evidence/phase02/offline-start.linux.log),
[restart HTTP server log](evidence/phase02/offline-restart.linux.log), and
[first offline installation log](evidence/phase02/offline-install.linux.log).
The report records Linux explicitly, `windows_launcher_executed: false`, runtime
source/lock hashes and both clean exit codes. Each HTTP pass compares full JSON
with approved fixtures, checks allowed/disallowed CORS, request errors and
reproducibility. It uses a temporary source copy with spaces in its path and a
fresh virtual environment; local wheels are used for a separate first offline
installation. Offline HTTP launches use `--offline` and `PIP_NO_INDEX=1`.

The launcher now isolates the server process group, forwards an interruption
once and waits for graceful Uvicorn shutdown before returning. The probe requires
the shutdown-complete log and a released port before restarting. Linux passed;
the Windows Ctrl+Break/`start.cmd` path awaits its actual CI runner. The two added
API tests freeze v1's rejection of the unapproved variable-demand profile fields.
No equation, response shape or generated fixture changed.

Baseline fixture: 24 kWh, 0.8 initial SOC, 0.2 minimum SOC, 0.95 discharge
efficiency, 1.5 kW critical load, no PV, continuous 12-hour outage, noncritical
shedding. First critical failure is **2026-01-01T09:07:12Z**. Delivered critical
energy is 13.68 kWh; unserved critical energy is 4.32 kWh; maximum per-interval
balance residual is below 1e-15 kWh. Values are synthetic simulations.

The suite explicitly checks immediate power-limited failures, arbitrary
constraint-derived depletion times, battery charge/discharge bounds, both
efficiencies, shared inverter throughput, critical priority, deliberate
shedding, zero grid during outages, incompatible PV, missing PV, grid recovery,
full/empty storage, curtailment, independent AC/storage/system conservation,
nonfinite and invalid inputs, error serialization, timezone normalization,
deterministic replay, parallel calls and comparison censoring. It also injects
an inconsistent dispatch to confirm that conservation violations fail the run.

Two unreachable defensive engine branches are uncovered: a non-positive event
interval and a cumulative-only residual over tolerance after every per-row
balance has passed. No conservation guard is disabled for testing.

One upstream Starlette/AnyIO deprecation warning is emitted by TestClient; it
does not affect test results. The local Playwright browser download was
unavailable, so browser-suite results are taken from the actual GitHub Actions
run, not claimed as a local pass. Native Windows execution has not been run
in this environment. The proposed two-platform workflow runs the same complete
launcher/HTTP probe, including Windows setup, shutdown and offline restart,
once the workflow owner enables it. [RELEASE.md](RELEASE.md) records the precise
PR #7 compatibility findings and coordination links.

The complete Python CI job is supplied as `docs/physics/simulation-ci.yml`.
It is intentionally not active under `.github/workflows/`, which is outside
the paths owned by Issue #2. The existing workflow only runs the legacy
physics tests, so those green checks alone do not certify this new service.
Use the local check command above until the proposed job is enabled.
