# Phase 04 release review

## Integration record

The candidate branch starts from `origin/main` at `dadf01d` and keeps the three team branches intact. It merges Beksultan's official Physics API PR #6 at `ef23a71` through `fe8ba86`, then the cinematic frontend PR #8 at `92613f0` through `ac95469`. The numerical source is `lastlight-dispatch-1.0.0` with schema `1.0.0`.

Askar's PR #7 at `7147b3f` has a separate dispatch implementation and a checkpoint built for physics/schema 1.1.0. The candidate takes its bounded physical Failure Frontier idea through the reviewed adapter in [FRONTIER.md](../../docs/physics/FRONTIER.md). It makes one official v1 trace per SOC column and classifies each shorter horizon as an exclusive trace prefix. No 1.1.0 metadata is accepted as compatible, no ML result is displayed, and no unsupported speed claim is made. The official engine, frozen baseline/comparison fixtures and existing numerical contracts were not replaced.

The production Physics API workflow is enabled at `.github/workflows/simulation.yml` for Ubuntu and Windows. It runs the official check and fresh HTTP launcher checks. CI results should be read from the pull request before merging.

## Visual and interaction review

The [before](before) and [after](after) folders contain the clinic, small business and residential selected states at 1366×768, 1440×900 and 1920×1080. They use the same selected site and viewport, with changed camera poses because the previous poses did not center the selected subject. `layout-metrics.json` records the selected site, camera state, element bounds and browser errors for every after capture.

The original city fabric intruded into the selected parcels, the special sites shared generic boxes, and the camera offsets pointed past the selected subjects. The candidate keeps every site's world coordinates but clears the parcels, gives the clinic a care canopy and cross, gives the commercial building a street-facing storefront and sign, and defines residential as a three-block parcel with one boundary. The selected facility is now the visual subject at each tested viewport. The 12ui review produced two design alternatives; the final pass used its hierarchy and contrast feedback while retaining the district's physical scene and existing visual language.

The creative handoff branch `creative/issue-4-visual-kit-handoff` was inspected at `3212a86`. It has procedural concrete maps and school facade/PV changes. Its own review says the concrete is still too blotchy and not approved. The original external visual kit binaries are absent. Those changes were not merged into this candidate, so the working school materials, roof geometry and energy visuals are preserved for the final demonstration.

Clinic, small business and residential are explicitly marked as visual site studies. Their outage and physics actions are unavailable. The school alone has the validated physical run, its original building materials and the baseline/upgraded playback. The opening label reads `ILLUSTRATIVE SCENE / NO PHYSICS RUN LOADED`; the instrument keeps `LIVE PHYSICS` and `VERIFIED OFFLINE REPLAY` as separate states.

[Recorded browser walkthrough](after/release-walkthrough.webm) includes district entry, inspection of all three visual sites, school inspection, outage, playback past the 9.12-hour failure, the 36 kWh upgrade, Failure Frontier and reset. [Frontier frame](after/frontier-1440x900.png) shows the physical classification. Browser screenshots are captured from the running React Three Fiber app using Chromium with WebGL, not a static render.

## Checks run locally on Windows

- Official production suite: 129 tests passed, 12 contract and fixture files verified, 99.44% coverage.
- Fresh launcher integration: 20 checks passed, including hash-locked offline installation, two live HTTP runs, graceful shutdown and released port.
- Web: lint and production build passed. The production bundle emits a large-chunk advisory; it is a size warning, not a build failure.
- Browser: 16 Playwright tests passed; the conditional live API test was skipped in the offline suite and passed separately against the running official API.
- Viewport review: clinic, small business and residential inspected at 1366×768, 1440×900 and 1920×1080. Critical controls remained visible and browser page errors were absent.

## Presenter launch

From the repository root, open two PowerShell terminals. In the first, run `.\services\simulation\start.cmd` (or add `--offline` after the initial install). In the second, run `cd apps/web`, `npm ci`, then `npm run dev`. Open the Vite address. For an API-free rehearsal, append `?demo=offline`; the app labels checked-in official results as `VERIFIED OFFLINE REPLAY`. See the root [README](../../README.md) for commands and requirements.

## Remaining limits

The three non-school sites have no verified electrical model. The district geometry and geography are illustrative, without measured site data or real utility topology. Marsel's original visual kit is absent from GitHub, and the review branch's substitute facade is unapproved. ML proposals remain unavailable until a checkpoint is adapted to official v1 and independently verified. The frontend bundle is still large; splitting it is separate from this release's numerical and presenter checks.
