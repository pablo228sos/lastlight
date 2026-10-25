# LASTLIGHT final demo release check

## Reviewed source

- Base: PR #13, `479e8d1fdbb0c357f61468c8934a314f345a15ed`.
- Visual source: PR #15, `9f34e4827eea6c4fff449e8bea111080311e7ad3`. Street and lighting components were adapted; the older whole-world scene was not copied.
- Analytical reference: PR #14, `e788cb0`. Readable verdict and map presentation were adapted against official v1. The experimental 1.1 engine and ML endpoint were excluded.
- Bounded official design search: PR #17, `390d1e7a2636b34e3aaa8d77453dbd1c4ee2758e`, merged into this review branch as `372ed10`. Its [Physics API CI run 40115858905, attempt 2](https://github.com/pablo228sos/lastlight/actions/runs/40115858905) passed on Ubuntu and Windows before integration.

## Local verification

- Production Python check after PR #17 integration: 160 passed, 99.45% coverage, 14 contracts and fixtures checked.
- Web build: passed with 594 modules. Vite reports a nonblocking large-chunk advisory.
- Web lint: passed without findings.
- Full Playwright smoke suite with local live API enabled: 23 passed in 7.9 minutes on Windows. This includes live HTTP, explicit offline replay, site honesty, camera motion, equipment, physical verdicts, Frontier, export, responsive layouts and video capture.
- Second targeted capture run: 4 passed in 6.0 minutes. It saved sample JSON reports and checked longer holds on the Frontier, report and reset states.
- Clinic parcel correction: build and lint passed; 10 targeted Playwright checks passed on Windows, including all three visual sites, responsive controls, verified replay, live API comparison and the school recording.

## Visual evidence

The original PR #13 failure frame at the same equipment camera is in `before/`. The `after/` set contains connected school, initial outage, served critical demand, observed 09:07:12 failure, 36 kWh comparison, 273-cell physical Frontier, evidence drawer, reset and live four-capacity search. Failure and comparison are captured at 1366×768, 1440×900 and 1920×1080. `offline-walkthrough.webm` (63.3 s) and `final-demo-walkthrough.webm` (73.4 s) are direct Chromium recordings of the running WebGL app. Inspected live video frames show equipment inspection at 25 s, upgraded result at 40 s, capacity search at 50 s, completed Frontier at 54 s, report at 60 s and reset at 70 s.

The later clinic visual QA uses `clinic-tree-before-1440x900.png` and `clinic-tree-after-1440x900.png` at the same facility camera. Procedural trees are now kept clear of all authored facility parcels by a margin larger than their crown radius. The school location, camera and physics code were not changed.

## Boundaries

- All displayed calculations are for synthetic school inputs. Geometry and the 12 visible PV modules are illustrative; official solar input is zero in this run.
- Clinic, business and residential cluster are visual studies, without a validated facility simulation.
- The 32 kWh selection is the smallest passing capacity among four explicitly tested candidates. It is not a price or global optimum.
- The presentation computer, GPU, projector and any external data feed have not been verified here. The offline route is the demonstrated fallback.
- Experimental ML claims, measured outage reduction, field deployment and commercial claims are outside this release.
