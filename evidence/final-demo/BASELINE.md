# Final demo baseline

Base commit: `479e8d1fdbb0c357f61468c8934a314f345a15ed` (PR #13, `integration/release-candidate`).

This worktree was created from that exact commit on `integration/final-demo-hardening`. PR #13, `main` and teammate branches remain unchanged.

Verified remote checks on the base commit:

- [Physics API run 40096664592](https://github.com/pablo228sos/lastlight/actions/runs/40096664592): passed on Ubuntu and Windows, including production tests, hashed-wheel setup, live HTTP and offline restart.
- [Verify run 40096664610](https://github.com/pablo228sos/lastlight/actions/runs/40096664610): passed web build, lint, Playwright and reference physics jobs.

Local reproduction from this worktree, before implementation:

```powershell
cd apps/web
npm ci
npm run build
npm run lint
npm run test:smoke
```

```powershell
# From the repository root, with the locked Python environment installed:
python -m services.simulation.check
```

Local baseline results on Windows 11:

- `npm ci`: 94 packages installed, zero reported vulnerabilities.
- `npm run build`: passed (589 modules; Vite reports a large-chunk advisory).
- `npm run lint`: passed.
- `python -m services.simulation.check`: 129 tests passed, 99.44% coverage, 12 checked contract and fixture files.
- `npm run test:smoke -- --reporter=line`: 16 passed, 1 skipped in 10.9 minutes. The skipped test requires a separate live Physics API server. Browser tests were run with a local Vite server at port 4173.

Baseline WebGL captures from the official school flow are in `before/`. The scripted camera was the unchanged PR #13 equipment shot. These images are preserved separately because the smoke tests regenerate older tracked evidence files.

The previous release review and WebGL evidence are in `evidence/phase-04`.
