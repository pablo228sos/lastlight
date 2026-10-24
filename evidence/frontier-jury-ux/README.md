# Failure Frontier jury UX: browser evidence

Actual Chromium screenshots, captured on 24 October 2026. Before and after use
the same synthetic school reference: 80% initial charge, a 16-hour window,
zero solar, and the real 9.12-hour first failure. The selected trace interval
starts at zero. These are browser captures of the existing 3D application,
not generated designs or substituted physics results.

The before captures use ML-branch commit `7147b3f`. After captures use the built
`feat/frontier-jury-ux` frontend with the same local FastAPI service. AI comparison
and proposal captures use actual existing model/API responses.

| Capture | What to inspect |
|---|---|
| [Before, 1366×768](before-1366x768.png) | Narrow panel, scrolling, tiny chart and unclear axes |
| [Before, 1440×900](before-1440x900.png) | Same reference school and original physical map |
| [Before, 1920×1080](before-1920x1080.png) | Original projector presentation |
| [Overview, 1440×900](overview-1440x900.png) | Trace-derived verdict beside the unchanged school |
| [Verdict, 1440×900](verdict-1440x900.png) | 9.12-hour first failure, 6.88 hours remaining, actual interval timeline |
| [Physical map, 1366×768](map-1366x768.png) | Both axis titles, real range, distinct current-run marker |
| [Physical map, 1440×900](map-1440x900.png) | Readable map and legend, patterns, discrete failure-time ticks |
| [AI comparison, 1440×900](ai-1440x900.png) | Actual model score/version and independent physics conclusion |
| [Checked AI cases, 1920×1080](map-ai-1920x1080.png) | White circles from real independently verified candidates |
| [Narrow report, 390×844](map-390x844.png) | Same interactive map in a single-column scrollable report |

## Checks executed

- Frontend build (including TypeScript): passed. Existing large-bundle warning remains.
- Frontend lint: passed.
- Complete local Playwright suite: **11 passed, 1 intentional media-recording skip**
  in 3.6 minutes. Existing camera, geometry, keyboard, projector and unavailable-
  backend checks are retained. New tests cover actual AI requests, checked overlays,
  unavailable AI, changed domains/profiles, survival, recovery, responsive layout
  and dialog/cell keyboard focus.
- `git diff --check`: passed. Physics/API/ML packages, checkpoint and scene files
  are unchanged relative to `7147b3f`.
- Main text and control contrast was checked numerically; patterns and explicit
  labels supplement color. Visual success was reviewed from actual captures.

The chart displays discrete tests. The current-run diamond may lie between cells;
it is backed by its own calculation. Short ticks do not interpolate between
charges. AI-selected cases are synthetic test inputs, not historical blackout
measurements, and their number is not a model-accuracy statistic.

[Implementation notes](../../docs/FRONTIER_JURY_UX.md) ·
[Draft PR #14](https://github.com/pablo228sos/lastlight/pull/14)
