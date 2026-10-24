# Issue #4 — real WebGL visual capture QA

This folder contains the workflow instructions for the **facade PR**, not a promise of finished visual quality.

### GitHub artifact

1. Open the PR's **Checks** tab and find `Issue 04 — WebGL visual captures`.
2. Open its workflow run. Under **Artifacts**, download `issue04-real-webgl-review`.
3. Compare `01-facility-connected-canvas.png`, `02-facility-blackout-canvas.png`, `03-facility-reset-canvas.png` — these use the same facility shot ID; the material, geometry and framing must remain continuous.
4. Inspect `04-equipment-canvas.png` for panel/cabinet detail.
5. Use the `-with-ui.png` files to verify UI overlays and the explicit `SYNTHETIC, NOT PHYSICS` label.
6. Read `capture-manifest.json` for commit SHA, camera state, frame dimensions and sizes.

**The screenshots are actual render output only when the GitHub workflow succeeds.** They are uploaded as Actions artifacts, not automatically committed to `main`. The supplied old `evidence/phase-00.5` reference frames are from a prior capture (and some use the **equipment** camera). Do not assert the old reference is pixel-aligned with the facility shot. Do not treat light changes as physically verified energy data.

The test verifies non-empty PNGs, actual canvas dimensions, expected camera state IDs, outage/reset state and absence of browser page errors. It cannot approve the aesthetics or calculate geometric reprojection on its own.

The ordinary `npm run test:smoke` suite skips this special test unless `ISSUE04_CAPTURE=1`, so standard CI behavior is preserved. The separate workflow specifically enables it.

Manual acceptance checks: no new buildings; 12 roof PV meshes still visible in their original 2×6 arrangement; no missing texture faces, jarring UV seams, motion discontinuities, blown highlights, or changes in school roof/fence/court/window placements. Compare with rendered footage and code invariants before marking ready.
