# Issue #4 — Iteration 05 / genuine WebGL capture review

**Status: browser-capture milestone PASSED; aesthetic approval NOT YET GIVEN.**

- Source branch: `creative/issue-4-visual-kit-handoff`, PR [#9](https://github.com/pablo228sos/lastlight/pull/9).
- Workflow run: [Issue 04 — WebGL visual captures / 40094128540](https://github.com/pablo228sos/lastlight/actions/runs/40094128540) — **success**.
- Separate [Verify / 40094128543](https://github.com/pablo228sos/lastlight/actions/runs/40094128543) — **success** (build/lint/smoke/physics-reference tests).
- Download the `issue04-real-webgl-review` artifact from the capture run (9 files; 30-day retention). The actual files are stored as GitHub Actions artifacts, **not** in the git tree.
- Capture source: `apps/web/tests/issue04.visual.spec.ts`; CI workflow: `.github/workflows/issue04-visual-review.yml`.

## Real-world frames (WebGL, 1920 × 1080)

| File stem | Shot ID | Phase | Grid | Size in PNG bytes |
| --- | --- | --- | --- | ---: |
| `01-facility-connected` | facility | SITE | 0 | 541,151 |
| `02-facility-blackout` | facility | BLACKOUT | 1 | 524,914 |
| `03-facility-reset` | facility | INSPECT | 0 | 542,115 |
| `04-equipment` | equipment | INSPECT | 0 | 653,363 |

Every stem has `-canvas.png` (WebGL only) and `-with-ui.png` (whole app); `capture-manifest.json` records states and capture time. Note: manifest `commit` under GitHub's pull_request workflow can be the **test merge SHA**, not the PR's `head_sha`.

## Observations from the artifact

1. **PASS (source-locked shape on this capture):** The original school body, right annex, rooftop 2×6 PV placement, fence, courtyard and district buildings remain in the same visible positions across facility shots. This is a visual inspection; an automated mesh-identity audit was *not* run.
2. **PASS (state):** District windows/streetlights darken on blackout while emergency school windows remain teal; reset restores connected-state illumination. This tests a synthetic visual rehearsal, **not real battery output**.
3. **NEEDS ART CORRECTION:** The main concrete walls and annex display prominent, cloud-like mottling. It still looks stylized rather than premium architectural concrete. First next action should be **reduce low-frequency albedo contrast**, using the same UVs and same meshes; capture again.
4. **FUTURE, NOT THIS ITERATION:** Surrounding apartment blocks, roads, poles, and night lighting remain stylized. Do not add or relocate any architecture in future polish.

## Optional pixel diagnostics (not a quality metric)

Computed from downloaded **canvas-only** RGB files using 8-bit BT.709 weighted luminance. All frames are 1920×1080; average pixel luminance:

- Facility connected: **25.00 / 255**
- Facility blackout: **23.44 / 255**
- Facility reset: **25.01 / 255**
- Equipment: **32.13 / 255**

These values only corroborate a changed scene lighting state. Since most of the frame is dark and view sizes differ, they do **not** measure school energy performance, physical realism or perceptual quality. The image-space connected-vs-reset PSNR of approx. 27.25 dB should **not** be used as a geometry-certification score (WebGL render variations).

## Remaining acceptance gate

Leave PR #9 as **draft**. Abai visually checks all four actual canvas captures plus the UI frames, confirms material repetition/edge behavior and responsiveness, then accepts or requests a single-facade albedo refinement. This artifact is not an AI-generated scene.
