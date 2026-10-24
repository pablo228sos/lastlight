# Cinematic integration review

This set records a real Chromium session against the running React application. It covers the district, the school, and a synthetic grid loss. The connected and disconnected school frames at each viewport use the same completed facility camera shot.

| Viewport | Connected | Disconnected |
| --- | --- | --- |
| 1440 × 900 | `school-connected-1440x900.png` | `school-disconnected-1440x900.png` |
| 1920 × 1080 | `school-connected-1920x1080.png` | `school-disconnected-1920x1080.png` |

`district-1440x900.png` shows the preceding site selection state. `school-rehearsal.mp4` is a 24.7 second review cut of the recorded browser session, played at 1.7× to keep the transition compact. The unedited recording is produced locally as `school-rehearsal.webm` by `cinematic-integration.spec.ts`.

## Review

- The school now has masonry facades, classroom bays, a defined entrance, PV cells, a mechanical roof unit, a service wing and a planted courtyard.
- Street trees and district masses have more variation. Road markings share a single instanced draw call.
- A camera completion signal lets visual tests capture settled poses rather than images from the middle of a move.
- The blackout changes lighting at a fixed camera pose. The visual state is a rehearsal; it does not assert physical performance.

## Still open

- The background city needs authored architectural assets and geographic specificity. Repeated blocks remain visible.
- Equipment and power flow need the validated simulation trace from the physics integration branch before numerical claims or status labels can be shown.
- Frame rate and WebGL fallback need review on the presentation machine with its actual GPU.
- Final creative approval is pending review of the running scene and these captures.
