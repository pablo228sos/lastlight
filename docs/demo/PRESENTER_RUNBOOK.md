# LASTLIGHT final demo runbook

## Windows launch

Install Python 3.12 and Node.js 20.19 or newer. Open two PowerShell terminals at the repository root.

Terminal 1:

```powershell
.\services\simulation\start.cmd
```

Wait for `http://127.0.0.1:8000/health` to respond. The first install needs package access. A previously installed API environment can be started without the package index:

```powershell
.\services\simulation\start.cmd --offline
```

Terminal 2:

```powershell
cd apps\web
npm ci
npm run dev -- --host 127.0.0.1 --port 4173
```

Open `http://127.0.0.1:4173/` in Chrome. Keep both terminals open. A live run is identified by `LIVE LOCAL PHYSICS API` in the app. If the API is unavailable, open `http://127.0.0.1:4173/?demo=offline` to use frozen official results. An API failure in live mode shows an error and an explicit `USE VERIFIED REPLAY` action; the app never silently substitutes a fixture.

## Presenter path

1. Enter the lab and fly into the district. Select the School.
2. Inspect rooftop PV, inverter and storage. The visual array has exactly 12 physical modules; the reference simulation has zero solar generation.
3. Disconnect the grid. Confirm the live or offline source label before citing any number.
4. Scrub to just before 09:07:12. Critical load remains served at 1.50 / 1.50 kW.
5. Use the failure marker or scrub just past 09:07:12. The 24 kWh, 80% starting-charge baseline has its first unmet critical demand. Its end-of-window unserved energy comes from the engine summary.
6. Compare the 36 kWh upgrade, then scrub to 12:00:00. There is no observed critical failure within the 12-hour test. The analytical 13.68-hour figure is not the observed test result.
7. In live mode, open `FIND VIABLE CAPACITY`. The official API tests 24, 30, 32 and 36 kWh with the same scenario. The smallest passing member is 32 kWh. This is a tested-set capacity choice, not a cost optimum. Close the panel.
8. Open the Failure Frontier. The diamond is the 80% charge, 12-hour baseline case. The 273 classifications come from 13 official physics traces. The right boundary is exclusive.
9. Open Data & Methods and download the JSON report. It includes resolved inputs, complete trace, model versions, provenance, hashes, result, comparison, any live capacity search and limitations.
10. Close the drawer and reset the scene.

At any point, `R` resets the scene and `Escape` returns to the city or closes the active drawer. The first calculated school run has a clear source label. Other facilities are visual studies and do not offer a physics outage.

## Capture and fallback

The still captures in `evidence/final-demo/after/` cover connected, initial outage, served critical demand, observed failure, comparison, Frontier, report and reset at 1440×900; failure and upgrade are also captured at 1366×768 and 1920×1080. `final-demo-walkthrough.webm` records the live API path, and `offline-walkthrough.webm` records the replay path. The baseline reference at the unchanged PR #13 equipment camera is in `evidence/final-demo/before/`.

For a disconnected presentation, keep the web app and the checked-in offline fixture available. Test the exact presentation computer, GPU acceleration, screen scale and projector connection before going on stage. Local browser evidence was recorded on Windows with Chromium's software WebGL path; it is not a claim that the venue machine has been tested.
