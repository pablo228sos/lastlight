# LASTLIGHT presentation asset provenance

## Source and capture

- Source repository: `https://github.com/pablo228sos/lastlight`
- Source branch: `integration/final-demo-hardening` (PR #22)
- Exact source commit: `0463d42282b371b57c68de7b1a9ba0323e09fd60`
- Source CI checked before capture: Verify run `40167735650` and Physics API run `40167735717`, both successful.
- Capture: actual application in headless Chrome at 1920 × 1080, WebGL 2 rendering with SwiftShader, local Vite at `127.0.0.1:4173`, and the official local Python Physics API at `127.0.0.1:8000`.
- The capture script waited for the WebGL canvas, the camera-idle state, the relevant live API response and UI visibility. It reported zero browser errors. See `capture-verification.json` and `../tools/capture-real-app.mjs`.
- Model: `lastlight-dispatch-1.0.0`; API schema: `1.0.0`. The school and all input data are synthetic. These are simulation results, not measurements from a deployed school.
- The working application, PR #22 branch, physics engine and original deck were not edited. The graphics were made on the isolated `assets/final-slide-evidence` branch.
- The original PDF has 14 pages at 1440 × 810 pt (16:9). We also supplied square crops for Canva frames.

## Numerical evidence

The real design-search response is saved at `../03-optimization/design-search-response.json`. The request uses a 12-hour outage, 1.5 kW critical load, 80% initial charge, 20% minimum charge, 95% discharge efficiency, 0 kW solar and the explicit candidate set 24, 30, 32, 36 kWh. The official endpoint returned:

| Capacity | Result inside 12-hour window | First critical failure |
| --- | --- | --- |
| 24 kWh | Failed | 9.12 h = 09:07:12 |
| 30 kWh | Failed | 11.40 h |
| 32 kWh | Passed | Not observed |
| 36 kWh | Passed | Not observed |

The endpoint selected **32 kWh as the smallest passing member of this tested set**. This is not a global optimum, a price recommendation or proof of autonomy beyond 12 hours. The API uses an exclusive observation horizon.

The real Failure Frontier response is saved at `../02-failure-frontier/frontier-data.json`. It contains 273 physics-verified cells from 13 official physics traces, across initial battery charge and outage duration. `frontier-clean-chart.png` and `slide08-frontier-square.png` draw each stored classification directly. There is no interpolation or ML prediction in these charts.

## Files

**01-inside-lastlight**

- `school-hero-original.png`: unmodified real school WebGL capture.
- `school-connected-original.png`: unmodified connected-state capture.
- `school-blackout-original.png`: unmodified disconnected-state capture at the same camera and viewport.
- `school-equipment-original.png`: unmodified equipment inspection capture.
- `slide05-hero-square.png`: 2000 × 2000 composition from the real school capture.
- `slide05-before-after.png`: 1920 × 1080 matched-camera comparison. Both source captures are cropped identically.

**02-failure-frontier**

- `frontier-original.png`: unmodified actual application capture.
- `frontier-data.json`: official response captured from the live application request.
- `frontier-clean-chart.png`: 2200 × 1400 chart redrawn from all 273 exact cells.
- `slide08-frontier-square.png`: 2000 × 2000 slide composition from the same cells.

**03-optimization**

- `design-search-original.png`: unmodified actual application capture with the real Python API.
- `design-search-response.json`: official response captured from the same application request.
- `battery-comparison-chart.png`: 1920 × 1080 four-candidate comparison from the response.
- `slide09-optimization-square.png`: 2000 × 2000 result composition with a crop of the authentic screenshot.
- `slide09-hero-result.png`: 1920 × 1080 result composition with a crop of the authentic screenshot.

**04-fallback**

- `first-critical-failure-original.png`: unmodified real WebGL failure-state capture.
- `first-critical-failure-presentation.png`: 1920 × 1080 fallback frame using that capture.

The originals are kept separate from designed versions. `../tools/render-graphics.mjs` checks the saved numerical responses before rendering the charts. `capture-verification.json` records the capture summary.
