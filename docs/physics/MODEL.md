# Dispatch model 1.0.0

This service owns production simulation equations. The legacy simulator is
loaded only by an independent regression test. It is never imported by the
engine, API or ML code. This is a deterministic quasi-static energy balance,
not voltage, frequency, thermal, degradation, short-circuit or transient power
flow analysis. It assumes constant efficiencies and immediate dispatch/load
shedding. It does not instruct or control real electrical equipment.

## State, units and topology

`capacity_kwh` is nominal internal DC capacity C. The stored energy E satisfies
`C * minimum_soc <= E <= C * maximum_soc`. Both efficiencies are applied once;
there is no extra invisible inverter efficiency. Power fields are AC-equivalent
bus-side kW. SOC and efficiencies are fractions. Usable full-window capacity is
`C * (maximum_soc - minimum_soc)`; initially available DC energy is
`C * (initial_soc - minimum_soc)`. The baseline starts with 14.4 kWh available
above reserve and can deliver 13.68 kWh AC.

The abstract hybrid converter has a single AC-equivalent throughput budget:

`accepted_solar_kw + battery_discharge_kw + grid_charge_kw <= inverter.max_kw`

Solar sent to the battery is counted once in accepted solar. Grid charging is
the opposite AC-to-storage conversion and consumes the same budget. Battery
charge is also limited by `battery.max_charge_kw`; discharge by
`battery.max_discharge_kw`. A grid-to-load bypass has its own
`grid.import_limit_kw` and does not consume the converter budget. Charging and
discharging never occur simultaneously. Export is disabled; unusable PV is
curtailed, including blocked islanding generation. This is a declared aggregate
topology; it is not a model of every vendor's hybrid inverter. Do not use AC
coupled equipment with different paths/ratings without revising this topology.

Without a grid-forming (`inverter.islanding_capable`) inverter, storage and PV
are disconnected during an outage. Solar has an additional compatibility flag:
PV works offline only when **both** `inverter.islanding_capable` and
`solar.islanding_capable` are true. When grid-connected, those flags do not
block ordinary conversion. `grid.online` / `profile_online` is the actual
state, even when the permitted import limit is zero. Therefore policy shedding
depends on grid state, not whether the import reading happens to be zero.

## Dispatch algorithm

For each piecewise-constant solar/grid input interval:

1. Set grid import capacity to zero when offline. Disconnect unsupported island
   sources. Apply noncritical shedding if the outage policy requests it.
2. Allocate available solar, then grid, then battery to requested demand, subject
   to the shared converter, grid import and battery discharge limits. Allocate
   the resulting service to critical demand first, then noncritical demand.
   No noncritical load is served while critical load has a shortfall.
3. If battery discharge is zero and storage has room, allocate surplus PV to
   charging. If grid charging is enabled, allocate remaining grid and converter
   headroom to charging. No grid export, hidden generation or load borrowing.
4. Compute internal energy rate `r = P_charge * eta_charge - P_discharge /
   eta_discharge`. Solve the linear time to the next SOC boundary. If it falls
   inside the sample interval, split there, advance E to that boundary and
   redispatch for the remainder. The last sample is clipped to the requested
   horizon. There are at most two output rows per requested input interval.
5. Integrate served/unserved energy over each actual segment. First critical
   failure is the start of the first segment with critical shortfall above the
   declared 1e-9 kW numerical tolerance. Keep simulating after failure, allowing
   later solar or grid recovery to be visible in the same trace.

This makes failure independent of whether the nominal step is 1, 15 or 60
minutes for constant inputs. It avoids spreading a partially depleted battery
over an entire interval and falsely classifying its beginning as a failure.
Power bottlenecks still cause immediate shortfall even with a fully charged
battery. No failure time or comparison result is hardcoded in the engine.

## Conservation equations

For each segment of duration dt hours:

```text
E_end - E_start = (P_charge * eta_charge - P_discharge / eta_discharge) * dt

AC residual = (P_grid + P_solar + P_discharge
               - P_critical_served - P_noncritical_served - P_charge) * dt

Loss = (P_charge * (1 - eta_charge)
        + P_discharge * (1 / eta_discharge - 1)) * dt

Combined residual = (P_grid + P_solar - P_critical_served
                     - P_noncritical_served) * dt - (E_end - E_start) - Loss
```

The separate storage residual is the difference between actual storage change
and the first equation. The API returns all three residuals, losses, source
energies, PV curtailment and unserved demand. The combined equation is also
checked over the whole run using accurate summation. A residual exceeding an
absolute 1e-8 kWh fails the run instead of returning inconsistent data.

Boundary energy is set from the solved event, never used to hide an energy
deficit. To avoid an artificial tiny failure segment at an exactly depleted
exclusive horizon, a boundary within `min(1e-12 hours, 1e-9 kWh / max(1, |r|))`
of a sample end is coalesced with that end. The actual residual still includes
that adjustment and must pass. Time summaries are rounded to 12 decimal hours;
the trace retains full floating-point power, duration and energy precision.
UTC rendering rounds to microseconds, so energy integration uses the returned
duration, not subtraction of timestamp strings.

Finite supported inputs are bounded to 0.001..20,000 kWh capacity,
0..50,000 kW per power field, efficiencies 0.01..1, 1 minute..168 hours duration,
and 1..60 integer minutes per requested step. These numerical/resource bounds
are part of the schema, not claims about specific hardware. Empty reserve
(`initial_soc == minimum_soc`) is valid and fails immediately unless another
source serves demand. A full battery is valid and curtails surplus PV. With
zero critical demand, coverage is defined as 1 and there is no failure.

## Analytic regression and censoring

For a continuous outage, no solar, critical demand only, an islanding-compatible
inverter and no power bottleneck:

`autonomy_hours = C * (initial_soc - minimum_soc) * eta_discharge / critical_kw`

| Case | Available DC energy | Delivered AC energy | Idealized autonomy |
| --- | ---: | ---: | ---: |
| 24 kWh, SOC 0.8 to 0.2 | 14.4 kWh | 13.68 kWh | 9.12 h |
| 36 kWh, SOC 0.8 to 0.2 | 21.6 kWh | 20.52 kWh | 13.68 h |
| 24 kWh, SOC 1.0 to 0.2 | 19.2 kWh | 18.24 kWh | 12.16 h |

This separately calculated analytic reference is never used to schedule a
failure. For the default 12-hour run the upgrades have no observed failure;
the API returns null observed survival and the explicitly idealized reference.
The 16-hour regression fixtures and tests observe all three physical events.

The model is independently compared with the archived equations for matching
constant/no-PV assumptions. Randomized tests independently reconstruct both
storage and AC/system balances from the public trace and check all bounds.
Measured site validation and review by a second teammate remain necessary
before presenting results as measurements or selecting real equipment.
