# School resilience: jury-facing analysis

The existing calculation is now explained in three chapters: blackout result,
Failure Frontier, and AI vs Physics. A compact verdict stays beside the school;
the larger report opens only on request. An optional three-step walkthrough
uses the same live requests and results as normal exploration.

## What the view means

- The verdict uses the returned survival flag, first failure and input horizon.
  Remaining outage time is the horizon minus the first failure, not a claim of
  continuous loss. The timeline renders every actual served/unserved interval,
  including recovery. A surviving run establishes survival only within its window.
- X is the initial battery charge, bounded by actual response samples; Y is the
  tested blackout duration. The reference map starts at 20%, not 0%. Axis positions
  use actual numeric values with half-cell padding at the edges.
- Mint dotted cells survive; orange hatched cells fail. The white circle means
  an AI-selected case independently rerun by physics. The dark diamond with a
  bright outline is the current school run, located continuously between samples
  when appropriate. Its separate calculation does not add a grid sample.
- Short black ticks mark failure times returned for individual sampled charges.
  No line interpolates between charge columns. Intermediate charge configurations
  are not independently verified by the chart.
- Hover, click/touch, focus and arrow keys expose the same cell information.
  Home/End traverse a row. A persistent inspector makes hover optional.
- RUN AI ANALYSIS posts the exact returned school input to the existing prediction
  endpoint. Its hash must match the current run. The score, model version,
  prediction and uncertainty/domain warnings are shown separately from physics.
- AI-suggested cases use the existing frontier endpoint and checked candidates.
  The overlay can be hidden. Counts are not accuracy, cases are not measured
  blackouts, synthetic scores are not real outage probabilities, and neither
  model output nor this chart authorizes equipment deployment.

## Implementation scope

`PhysicsPanel.tsx` provides the compact overview. `SchoolAnalysisReport.tsx` owns
the modal chapters and walkthrough. `OutageResult.tsx`, `FrontierChart.tsx`, and
`FragilityAnalysis.tsx` explain the three existing outputs. `analysisFormat.ts`
handles display formatting; `physics.css` retains the existing Manrope/Plex fonts
and scene palette with semantic status tokens.

`useSchoolSimulation.ts` adds the existing prediction request, independent busy /
error states, cancellation and generation guards. A missing model preserves the
physical answer. Frontier requests respect supplied profile horizons rather than
extending profiles to 24 hours. The physical frontier algorithm is unchanged.

`App.tsx` wires these controls and prevents scene keyboard shortcuts while the
modal owns focus. The dialog contains Tab navigation, closes with Escape and
restores the opening control. The underlying 3D controls remain available when
the report is closed.

`playwright.config.ts` accepts optional `LASTLIGHT_WEB_TEST_PORT` and
`LASTLIGHT_API_TEST_PORT` overrides so local verification can avoid other running
services. Defaults remain 4173 and 8000; the frontend test proxy follows the API
port. Existing production behavior is unchanged.

No physics/API/ML package, checkpoint, geometry, asset, lighting implementation,
coordinate, camera path or scene-state adapter is modified. No model is retrained
for this UX work.

## Verification and evidence

Verification results and actual same-scenario browser captures are recorded in
[the evidence index](../evidence/frontier-jury-ux/README.md). The reference uses
synthetic school inputs: 80% initial charge and a 16-hour calculation. Its actual
first failure is 9.12 hours, leaving 6.88 hours at that first event.

Local checks: `npm run build`, `npm run lint`, and the complete Playwright suite.
The complete suite passed **11 tests with 1 intentional recording skip**. After
the final small copy/layout adjustments, the connected-grid/recovery test and
four-viewport responsive test also passed independently. The initial UI commit
`d0bc6c4` passed both GitHub Actions jobs in
[run 40103270329](https://github.com/pablo228sos/lastlight/actions/runs/40103270329).
Latest-head checks remain visible on [PR #14](https://github.com/pablo228sos/lastlight/pull/14).

The new `frontier-ux.spec.ts` covers the real prediction endpoint, checked proposals,
domain-dependent axes/current marker, survival, early failure with later recovery,
model/API absence, focus handling and 1366×768 / 1440×900 / 1920×1080 / 390×844 layouts.
Variation tests replay real service calculations, never fabricated scientific
fixture values. Error-path tests explicitly simulate unavailable services.

Main text/surface contrast is 15.68:1; muted text/surface 10.40:1; muted text/raised
surface 8.78:1; button text/orange 8.98:1. Patterns and labels supplement color.
Manual visual review uses actual Chromium captures; other browsers and real
projector hardware are not claimed as tested. The pre-existing large bundle
warning remains. Detailed methodology and long candidate lists scroll inside
the report rather than covering its navigation controls.
