# Source and provenance

- Application: LASTLIGHT, `integration/final-demo-hardening`, commit `3bcc1e079edb95246a6b4875fbf5ac62506bc603` (PR #22). No application, 3D scene or Physics API source was changed to make this film.
- CI at capture: Physics API workflow `40159290442` and Verify workflow `40159290446`, both successful for this branch head.
- Fresh recording: `LASTLIGHT_SOURCE_WEBGL_1920x1080.webm`. Chromium recorded the running local WebGL application at native 1920×1080, 25 fps, 96.48 s. The application used the **live local Physics API**. SHA-256: `c6ac75e7e97cde4d2f632f4ea8118c8af4826e6006834874380d930aefa3b809`.
- Earlier unedited reference: `original-final-demo-walkthrough.webm`, copied without re-encoding from `evidence/final-demo/after/final-demo-walkthrough.webm`, 960×540. SHA-256: `ebc0438bffaab7766d427b1f35f94b68f35e7a85e62b718c18af94db304f5f88`.
- Live export from the captured run: `verified-live-school-report.json`. It identifies `Live local Physics API`, model `lastlight-dispatch-1.0.0`, schema `1.0.0`, synthetic inputs and exact hashes. SHA-256: `1bd994bf67830bb4966d436d7e728f7792a537d6e9079bb6209023c170e9c040`.
- Final edit: `LASTLIGHT_FINAL_DEMO_90S.mp4`. Six 15-second chapters from the same authentic browser recording, with only time remapping and editorial captions. No generated scene, invented forecast, voiceover or music. H.264 High, 1920×1080, 30 fps, yuv420p, exactly 90.000 s, 2700 frames. SHA-256: `995cee5b69dded272c2458e39c3916643adb9c6f2db80bf539e10d9ccb54b1b4`.

## Numerical claims shown

The synthetic school test lasts 12 hours. Baseline battery: 24 kWh, initially 80% charged, 20% minimum reserve; critical demand: 1.50 kW. The first unmet critical demand is observed at 9.12 hours = **09:07:12**. At 36 kWh, critical service survives the full 12-hour observation window. The live capacity search physically runs 24, 30, 32 and 36 kWh: the first two fail, the latter two pass, and **32 kWh is the smallest passing member of that tested set**. This is not a global optimum or a cost recommendation. Failure Frontier classifies **273 cells from 13 official physical runs**; the cells are not 273 independent API simulations.

## Editing map

The six chapters use these source ranges, respectively: `09.000–27.394`, `27.394–39.000`, `39.000–49.000`, `49.000–63.500`, `63.500–75.000`, `75.000–94.000` seconds. Each is mapped to 15 seconds. `render-demo.py` and `titles.ass` document the reproducible edit. The six numbered PNGs are untouched Chromium screenshots of the same live run. `report-export-evidence.png` is an additional screenshot of the actual export control.

The scene is illustrative, with no measured school or utility data. The physical outcomes are verified **for the stated synthetic inputs**, not field telemetry.
