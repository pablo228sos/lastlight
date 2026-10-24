# Dispatch model 1.1

This extends the reviewed team contribution `776caa4` on `feature/physics-api`.
The original branch is unchanged. Version 1.1 adds variable critical/noncritical
profiles and explicit physics-version/assumptions metadata; existing wire fields
and fractional SOC units are retained.

The default sampling interval is 15 minutes. Grid, PV and both demand profiles
are piecewise constant within each input interval. A profile overrides its scalar
fallback and must contain exactly `ceil(duration_hours * 60 / step_minutes)`
values. The last interval may be partial. Legacy 1..60 minute requests remain
supported for regression and convergence checks.

All source, demand, charge and discharge powers are AC-side kW. Battery energy is
internal DC kWh. Within an interval:

`dE/dt = charge_kw * eta_charge - discharge_kw / eta_discharge`.

The dispatch serves critical demand first, then noncritical demand unless the
outage shedding policy removes it. Solar is accepted before grid import; the
battery covers the remaining load. Surplus solar and optional spare grid import
can charge storage. Battery and PV operation during islanding require the
explicit inverter compatibility flags. Inverter, grid-import, charge/discharge
and minimum/maximum storage limits are enforced.

The interval is split at the exact minimum/maximum battery-energy event. Power
is redispatched after the event, so the baseline fails at 9.12 hours, rather than
at the next 15-minute boundary. Each trace row describes `[start, end)` and
contains start/end SOC and energy; there is no invented initial powered point.
Failure exactly at the exclusive horizon is right-censored, not observed failure.

Each row checks AC, storage and combined energy residuals; the complete run also
checks cumulative balance (absolute tolerance 1e-8 kWh). Conversion losses and
curtailment are explicit. Input hashes include resolved defaults and profiles;
run identity includes the version. The same input produces the same response.

This is a single-bus quasi-static energy model, not a certified network model.
It excludes voltage, protection, frequency/transient dynamics, degradation and
equipment startup. Caller provenance is a claim, not independent verification.
Synthetic profiles are never relabelled as measured building data.
