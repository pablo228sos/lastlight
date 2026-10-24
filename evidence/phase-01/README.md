# Phase 01 computational integration evidence

Actual production-build screenshots, captured on 24 October 2026 from Vite
preview with the local FastAPI service. The scene is the existing 3D world;
these are browser captures, not generated mockups.

- `school-calculated-1440x900.png`: initial outage interval, SOC 80%, 1.5 kW
  critical demand served, observed first failure 9.12 h.
- `critical-failure-1440x900.png`: first critical failure selected from the same
  trace, SOC 20%, critical demand unserved, calculated emergency lighting state.
- `frontier-proposals-1440x900.png` and `frontier-proposals-1920x1080.png`:
  exact physical grid and twelve real FragilityNet proposals independently
  checked by the physical simulator. Circles identify those checked proposals.

The input is the synthetic school reference, not measured building telemetry.
The map shows discrete verified samples; intermediate SoC configurations are
not independently certified. Foreground numerical values and scene lighting
come from the same selected run. The existing camera can continue its original
transition during capture; no camera path or geometry was changed.

Browser regression tests also exercise service unavailability, which explicitly
returns the application to labelled rehearsal without numerical results.
