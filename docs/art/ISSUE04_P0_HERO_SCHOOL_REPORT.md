# LASTLIGHT / Hero School P0 Production Review — 2026-10-24

**Status:** first substantive hero-school pass implemented, committed, WebGL-rendered, and visually compared. Review needed from Abai before incorporation into official Physics RC.

## A. Implemented on Draft PR #15

- `apps/web/src/scene/SchoolHeroDetails.tsx`: high-contrast but physically restrained window bay assemblies (same 8 original front + 3 emergency annex window centers), glass/frame/sill/mullion details, school entrance door architecture, roof parapet/edge trim, wall joints, gutters and technical cabinet hardware on the original two equipment coordinates. All introduced luminous materials and entrance lights respond to `visual.noncriticalLit` or `visual.criticalLit`.
- `apps/web/src/scene/SchoolFacadeWall.tsx`: removes the overly mottled active v02 facade materials and replaces them with deterministic, low-contrast, 256px tiling mineral-plaster material; existing two original box geometries and transforms are unchanged. The original v02 PNG maps still remain in the repository, but are inactive.
- `apps/web/src/scene/DistrictWorld.tsx`: uses hero details, removes duplicate simple front/annex window emission meshes, retains all other original site and 12 roof PV positions, and correctly gates the cabinet indicator on `visual.criticalLit`. Tempered global night ambient/directional lighting.
- `apps/web/src/scene/RealNightLights.tsx`: four real light sources precisely at **existing** streetlight positions near school `[-18,55]`, `[31,55]`, `[-18,-33]`, `[31,-33]`. Actual point lights only on when `visual.gridConnected`; absent entirely in lowPower mode. No new lamp towers.
- `apps/web/tests/issue04.motion.spec.ts` and `.github/workflows/issue04-motion-review.yml`: real 1366×768 Playwright/Chromium camera movement capture; produces real .webm and machine-readable camera position proof.

**Not modified:** physical simulation code, API schemas, school origin `[13,0,7]`, building body sizes, road axes, equipment centers, hotspots, 12 physical PV modules and 2×6 placement, camera shot definitions. Existing interactive orbit, zoom and pan stay within one scene.

## B. Real visual evidence, not AI

- [Prior PR #15 source-locked real screenshot run](https://github.com/pablo228sos/lastlight/actions/runs/40107951077) — baseline facility pose `[65,39,58]`, forward `[-.6400,-.4431,-.6277]`, 1920×1080.
- [Hero-school standalone screenshot run](https://github.com/pablo228sos/lastlight/actions/runs/40110659825) — **success**, exact same facility pose, 1920×1080. `issue04-real-webgl-review` artifact with five screenshots and JSON manifest.
- [Hero-school + corrected night lighting screenshot run](https://github.com/pablo228sos/lastlight/actions/runs/40111233343) — **success**, five actual WebGL frames at fixed canonical positions, connected/blackout/reset states.
- [Genuine laptop-sized 1366×768 WebGL video and camera-movement proof](https://github.com/pablo228sos/lastlight/actions/runs/40111369149) — **success**, artifact `issue04-real-webgl-motion-1366` contains `district-right-drag-1366x768.webm`, `district-before-pan-1366x768.png`, `motion-manifest.json`. Right drag changed camera position from `[81,63,83]` to `[90.38,63,66.342]` (movement 19.117 world units) without changing the district phase/shot.
- A companion matched-camera BEFORE/AFTER contact sheet is supplied to Abai in the ChatGPT conversation. It compares genuine WebGL reference frames, **not** generated AI concept imagery.

**Subjective observation:** Hero facade reads much more architecturally credible at the locked facility angle. It remains a simplified real-time model, not photogrammetric realism; apartments and street foliage still look synthetic. This is meaningful improvement, not a claim of completed AAA quality.

## C. Higgsfield provenance

Earlier connected Higgsfield `cinematic_studio_video` generated one 5-second, muted 16:9 image-to-video **concept** from the older `main/evidence/phase-00.5/keyframe-facility.png` image, job `4c94d565-20f3-4b37-8e2b-f50aa441bc65`, priced at 5 trial credits when submitted. Tool subsequently reported **completed**. This video is **not** an editable model, verified geometry reference, seamless material scan or a deployed game asset. **No Higgsfield-generated media has been integrated** in the WebGL code in this P0 pass. The high-impact real-time material pass uses procedural Three.js/CanvasTexture instead.

## D. Verification

- [Verify on hero and night lighting code](https://github.com/pablo228sos/lastlight/actions/runs/40111233348) — **SUCCESS** on commit `643bc08d`; build/lint/smoke + reference physics CI jobs.
- [Verify on 1366p camera test and workflow](https://github.com/pablo228sos/lastlight/actions/runs/40111369129) — **SUCCESS** on `2060113d`.
- [Motion workflow](https://github.com/pablo228sos/lastlight/actions/runs/40111369149) — **SUCCESS**.
- [WebGL capture on night-light code](https://github.com/pablo228sos/lastlight/actions/runs/40111233343) — **SUCCESS**.
- The canonical facility camera **position + forward vector** are identical in connected, blackout and reset frames; the original school front lit windows switch off, while the three emergency annex windows follow `visual.criticalLit`. Normal frames are restored upon reset.
- **No representative Windows laptop FPS measurement or renderer draw-call benchmark** is available. GitHub software-rendered CI performance is not a defensible real-device benchmark; do not claim 30 or 60 FPS. Point light count is capped and skips in lowPower, but that is an optimization hypothesis requiring measurement.

## E. PR #13 compatibility — DANGER: Do not cherry-pick DistrictWorld wholesale

Official PR [#13](https://github.com/pablo228sos/lastlight/pull/13) has **different, newer production architecture**:
1. `apps/web/src/App.tsx` passes a `visual` state from `usePhysicsRun`, not the PR #15 synthetic rehearsal.
2. Official `SchoolDetails.tsx` already has bespoke window treatment and its own `Photovoltaics()` loop of twelve modules. Blindly adding `SchoolSolarArray` could **duplicate the roof array**. Do **not** cherry-pick entire `DistrictWorld.tsx`.
3. PR #13 `SHOTS.facility` has camera position **`[78,50,73]`**, PR #15 used **`[65,39,58]`**. Even exact-registered PR #15 screenshots cannot certify visual composition at PR #13's canonical facility camera.
4. Official PR #13's `VisualRehearsalState` includes `kind:'physics_trace'` and the same `gridConnected/noncriticalLit/criticalLit` property names. The hero's frame and light logic can be **adapted** under Abai's guidance to official state-driven renderers without touching simulator contracts.

**Recommended selective integration path for Abai:**
- In PR #13 keep `SchoolDetails.tsx` and production `DistrictWorld.tsx` as source of truth, then merge *only nonduplicate visual frame, glazing, plaster and entrance details* from `SchoolHeroDetails.tsx`/new `SchoolFacadeWall.tsx`, after reviewing overlap and aligning with the existing physical-school components.
- Audit all noncritical and critical emissive materials against official physics trace, including zero-critical-load transition and grid restore, not merely synthetic blackout.
- Re-capture at PR #13's new facility pose, equipment shot, and the official Failure Frontier scenario.
- Do not automatically merge PR #9 or #15, don't touch backend physics, and do not claim production-physics verification from this branch.

## F. Remaining limitations / next priority

- Architectural variety in nearby residential buildings still limited; realism below the requested aspiration.
- PV and school panels read as stylized dark modules, not survey-calibrated material models.
- Ambient lighting and lamp surface reflectance have not been tuned with measured HDR; screen-space atmospheric phenomena are deliberately avoided for laptop performance.
- No direct WebGL screenshot comparisons to PR #13's newer school camera.
- Need manual material/art review of the actual 1920×1080 and 1366×768 evidence with Abai and on representative Windows laptop (FPS, thermals, graphics quality and mouse latency).
- Better architectural variety and entrance landscaping are lower priority than getting this P0 hero layer selectively into the physics-connected release candidate without breaking energy semantics.

**Approval:** Draft PR #15 remains open, do not merge until Abai approves.
