# LASTLIGHT — Final Visual Acceptance / Release Compatibility Handoff

**Scope:** source-level review only plus official-release read-only WebGL acceptance; no changes to PR #13 (`integration/release-candidate`), PR #9, `main`, physics dispatch, ML, or camera system. PR #15 stays Draft.

## Authoritative source snapshots

| Subject | Repository path | Version |
|---|---|---|
| Official release | `integration/release-candidate` | `479e8d1fdbb0c357f61468c8934a314f345a15ed` |
| Official world | `apps/web/src/scene/DistrictWorld.tsx` | blob `345707ed82de9b7c97fe606939505c06e909d361` |
| Official school | `apps/web/src/scene/SchoolDetails.tsx` | blob `a243cecb58caf9e7440fc1e24130a19f15f297b6` |
| Official physics adapter | `apps/web/src/app/usePhysicsRun.ts` | blob `28402f529bb3fcb503cda75764be6e2764229dd6` |
| Review branch | `creative/photoreal-district-v1` | [Draft PR #15](https://github.com/pablo228sos/lastlight/pull/15) |

**Architectural source of truth is PR #13.** Do not cherry-pick or overwrite the `App.tsx`, `DistrictWorld.tsx`, `SchoolDetails.tsx`, `usePhysicsRun.ts`, `useMissionState.ts`, `CameraDirector.tsx`, `HotspotProjection.tsx`, or physics service from PR #15.

## Exact port decision by component

| PR #15 path/component | Decision for PR #13 | Why / required change |
|---|---|---|
| `SchoolFacadeWall.tsx` → `makePlasterTile`, `sameBoxWithPhysicalUV` | **ADAPT helper/material only** | Sober light mineral plaster is safe as an artistic option. PR #13 already has masonry facade panels in `SchoolDetails` on main front/right, annex side; don't layer fresh full building boxes over those planes or the source body; rebuild UVs on *official* geometry or replace just one currently rendered wall material after QA. Render can change due to bright wall tint/exposure. |
| `SchoolHeroDetails.tsx` → static trim helpers/`Batches` | **SELECTIVE ADAPT** | Source-bound deterministic geometry at local school origin, original main/annex sizes. PR #13 already has projecting courses, pilasters, window bays, canopy, doors, roof edge, annex windows. Remove every overlapping position *before* transferring the unobstructed subset; check z-fighting/overdraw and actual [78,50,73] camera. |
| `SchoolHeroDetails.tsx` → `WindowBay` equivalent, `FRONT_POSITIONS`, `EMERGENCY_POSITIONS` | **DO NOT PORT AS-IS** | Official front window centers `[-12,-8.8,-5.6,5.6,8.8,12] × [2.35,5.72]` = **12** official decorated bays; PR #15 uses `[-11,-7,7,11] × [2.1,5.6]` = **8**, in addition to an older simpler frontage. Official annex centers `[12.25,15.7,19.15]` @ y 3.25; PR #15 `[11.8,15,18.2]` @ y 3.4. Copying both duplicates/misaligns glazing. Borrow roughness/mullion design only, rebuild on official positions; preserve original state transitions. |
| `SchoolHeroDetails.tsx` → entrance `SchoolEntrance` | **ADAPT PARTS ONLY** | Official release already has decorated portal at local `[0,2.42,13.34]`, canopy posts and additional canopy roof at `[0,5.55,15.2]`. PR #15 duplicates door frame, handles, soffit and fixture at other elevations. Choose individual door-hardware details, preserve official entrance/canopy and path. |
| `SchoolHeroDetails.tsx` → cabinet trim `SchoolEquipmentDetails` | **ADAPT NONEMISSIVE HARDWARE ONLY** | Two official cabinet centers are school-local `[15.7,1.5,3.2]`, `[19.4,1.65,3.2]`; world `[28.7,1.5,10.2]` and `[32.4,1.65,10.2]`. Official `SchoolDetails` also adds cabinet bases/frames/lamps. Keep official original boxes and link projections; omit duplicate backplates and emissive panels. |
| `RealNightLights.tsx` | **ADAPT AFTER INSPECTION** | Four finite point lights at existing world positions `(-18,55),(31,55),(-18,-33),(31,-33)`, y 5.1, 22-world-unit range, no shadows, lowPower off. Original street lamp heads have world y 5.2. Correctly gate with *official* `visual.gridConnected`, but these are additional lights: need compare with PR #13 ambient, main school light and existing light-pool sprites to avoid clipping/performance surprises. Keep site coverage modest and no illumination from grid-powered lamps during outage. |
| `CityArchitecture.tsx` → `ArchitecturalBuildingBodies` | **ADAPT with official site list** | Procedural textured instanced mass respects input building transforms. Official `buildings` includes added parcel safety clearances around **clinic, business and residential** (PR #15's older building list omits the official-wide clearances); NEVER port PR #15's entire `buildings` generator, or you'd bury authored sites. Feed official `buildings` to this component, retain existing windows / tree geometry and verify brightness. |
| `CityArchitecture.tsx` → `ArchitecturalDistrictDetails` | **OPTIONAL SELECTIVE ADAPT** | Instanced sills/frames can fit derived official building dimensions; must align official seeded window centers, ensure no double-overlaid dark glass obscures emissive windows, measure calls with/without, and avoid balcony geometry intersecting signs/parcel paths. |
| `CinematicStreets.tsx` | **CONDITIONAL PORT** | Shares exact four road axes `[-80,-33,55,100]` and roadway widths, but adds sidewalks/curbs, zebra crossings, multiple materials. Replace original `Streets()`, do **not** render both overlapping road decks. Verify curbs stop at intersection and do not overlap site entrances, driveways, official authored facilities, or campus route. Check aliasing in official facility camera. |
| `SchoolSolarArray.tsx` and all PR #15 PV code | **DO NOT PORT** | PR #13's `SchoolDetails.Photovoltaics()` already emits **exactly 12 modules**, centers `x=-12+4.5*(i%6)`, `z=2.3+3.4*floor(i/6)`, school-local y 8.81. PR #15's 12-panel `SchoolSolarArray` would duplicate/occlude those 12; no new roof array. |
| `CameraDirector.tsx`, source camera shot definitions and mouse changes | **DO NOT PORT** | Official PR #13 facility preset is `[78,50,73]` targeting `[13,3,7]`; PR #15 has `[65,39,58]`. Keep official camera journey and interaction; never reuse synthetic-branch screenshot as matched PR #13 proof. |
| `DistrictWorld.tsx` as a whole | **NEVER CHERRY-PICK** | Official has new sites, physics-driven render state and `SchoolDetails`. PR #15 is built on an older synthetic branch; full-file replacement silently removes integrated release features. |
| PR #15 synthetic `issue04.visual.spec.ts` / motion screenshots | **NOT RELEASE ACCEPTANCE** | These may validate same PR #15 environment but do not certify official physics adapter or its critical-failure and reset states. Use new official evidence below instead. |

## Visual state wiring — production rule

1. Release `App.tsx` explicitly does `const visual = physics.visual ?? mission.visual`.
2. Before a run or after reset, `physics.visual` is null and `mission.visual` is the **illustrative presentation state**. Label connected/reset frames accordingly, not as an independently computed grid-online physical trace.
3. During outage, `usePhysicsRun` supplies `kind:'physics_trace'`; `gridConnected` tracks the authoritative trace; `noncriticalLit` goes out after grid disconnect, and `criticalLit` must follow **observed unserved critical load**, not battery color, elapsed timestamps invented in JS, or failure forecasts.
4. Baseline official replay/engine: first observed critical failure at 9.12 hours, explicit event-split trace rows; at 8.7 h critical served = 1.50/1.50 kW, at 9.121 h = 0/1.50 kW. End of observation is exclusive; no visible failure inferred exactly at boundary end.
5. School windows, emergency annex windows, roof emergency bars and equipment status/material emissions must follow the *same* official state, including blackout and loss of critical load. Existing PR #13 global cabinet power-line and indicators should be reviewed: some intentionally glow in a layer independent of the actual battery, and must not be mistaken for validated power availability.
6. PR #15 and PR #13 both have global ambient/hemisphere/directional fill that **does not shut off** with the grid. This is plausible moon/environment lighting; do not demand a black image to prove outage.
7. PR #13 `HotspotProjection.tsx` world anchors: battery `[35.5,5.5,10.3]`, inverter `[23.5,4.9,10.3]`, PV `[8,10.6,14]`. These are label/projector targets, not physical cabinet centers. Keep them intact until Abai approves an equipment-specific alignment review.

## Official camera and evidence

Official `SHOTS.facility.position=[78,50,73]`, `target=[13,3,7]` in release `useMissionState.ts`. The original official `CameraDirector` sets DOM `data-camera-idle='true'` when its GSAP motion completes; this is the camera-settlement signal for browser capture. **Important limitation:** the new capture does not instrument actual camera quaternion/position; the preset and settled marker are source-verified, not measured independently per frame.

New **read-only** acceptance:
- Source/test: `apps/web/tests/issue04.release-acceptance.spec.ts` on PR #15.
- CI: `.github/workflows/issue04-official-release-visual.yml` on PR #15.
- Runner checks out official **fixed** `479e8d1` SHA and PR #15 separately, installs official production Python service and official web dependencies, stages ONLY the Playwright test into the throwaway checkout, and runs the **actual localhost physics engine**. Abai's PR #13 and `main` are never changed.
- Six WebGL+UI pairs at 1440×900: `01-connected` (pre-outage illustrative presentation), `02-grid-disconnected` (live physics start), `03-critical-supplied` at 8.7 h, `04-critical-failure` at 9.121 h, `05-reset` (presentation state), `06-equipment` (official equipment view). Assertion gates cover `data-physics-source='live'`, `data-critical-lit`, actual 1.50/1.50 vs 0.00/1.50 and 09:07:12 observed failure.
- Reviewer artifact: `issue04-pr13-physics-webgl-acceptance`. Reference [CI run 40154843782](https://github.com/pablo228sos/lastlight/actions/runs/40154843782). Treat screenshots as **pending** until run passes and artifact appears; don't imply synthetic screenshots are evidence of the release.
- This captures the **unmodified official product**, not the appearance of selectively ported PR #15 assets. To measure their actual integration, Abai must apply an approved minimal subset on his own reviewed integration branch then repeat this test.

## Performance

A representative physical Windows laptop was **not available through these tools**. No vendor/model of Windows GPU, native screen capture frame-time distribution, Three.js `renderer.info.render.calls` values, or post-port delta was measured. The GitHub Ubuntu Actions software-rendered Chromium output **cannot** be presented as FPS/performance on a Windows laptop. Keep these cells as "not measured", not synthetic numbers.

If Abai can run a local machine, request Windows GPU + driver, CPU/RAM, browser version, 1366×768 and 1920×1080, frame-time distribution (p50/p95/p99), draw calls/triangles at same six states, and visual defects. Compare production before/after with identical camera quality and real physics state; reject port with materially unstable worst-case frame time.

## One visual recommendation for Abai

**Ship the physics-connected PR #13 first; cherry-pick only a restrained plaster finish and carefully de-duplicated trim/hardware that visibly improves the official facility camera, while preserving PR #13's glazing, PV count, cabinets, world sites and physics adapter.** Defer wholesale city/street overhaul and additional street point lights until a source-aligned side-by-side and a representative Windows FPS test pass.

## Review state

No official integration performed here. PR #15 remains Draft. Source review has identified the conflicts and created a safe read-only official capture harness. Actual WebGL capture/CI acceptance are determined by the workflow's latest conclusion and artifact, not assumed by this document.
