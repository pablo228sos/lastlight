"""Deterministic, event-split, single AC bus energy dispatch (no I/O or ML).

Inputs are piecewise constant over the requested sampling intervals. Each interval
is split at the exact time the battery reaches a SOC bound. No step-averaged
power shortfall or hardcoded failure time is used.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import fsum
from uuid import NAMESPACE_URL, uuid5

from . import MODEL_VERSION
from .schemas import (
    ComparisonDelta,
    ComparisonRequest,
    ComparisonResult,
    SimulationRequest,
    SimulationResult,
    SimulationSummary,
    SimulationTracePoint,
)

POWER_TOLERANCE_KW = 1e-9
BALANCE_TOLERANCE_KWH = 1e-8


class EnergyBalanceError(RuntimeError):
    """Internal invariant violation; never return a physically invalid trace."""


def utc_stamp(start: datetime, elapsed_hours: float = 0) -> str:
    return (start + timedelta(hours=elapsed_hours)).isoformat().replace("+00:00", "Z")


def canonical_input(request: SimulationRequest) -> str:
    """Hash fully resolved defaults, UTC normalization and strict finite JSON."""
    return json.dumps(
        request.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), allow_nan=False
    )


@dataclass(frozen=True)
class Dispatch:
    grid: float
    solar: float
    charge: float
    discharge: float
    grid_charge: float
    critical: float
    noncritical: float


def dispatch(
    s: SimulationRequest, energy: float, grid_online: bool, pv: float,
    critical_demand: float, noncritical_demand: float,
) -> Dispatch:
    """Critical priority, solar -> grid -> battery, with optional surplus charging.

    Hybrid conversion budget: solar accepted + battery discharge + grid-to-battery
    charge <= inverter.max_kw. Grid-to-load bypasses this budget. PV and storage
    are disconnected when islanded without a grid-forming inverter; PV also
    requires its own explicit islanding compatibility flag.
    """
    b = s.battery
    inverter_kw = s.inverter.max_kw if grid_online or s.inverter.islanding_capable else 0.0
    pv_kw = min(pv, inverter_kw) if grid_online or s.solar.islanding_capable else 0.0
    grid_limit = s.grid.import_limit_kw if grid_online else 0.0
    noncritical = (
        0.0 if not grid_online and s.load.shed_noncritical_during_outage else noncritical_demand
    )
    requested = critical_demand + noncritical
    solar_load = min(pv_kw, requested)
    grid_load = min(grid_limit, requested - solar_load)
    discharge = 0.0
    if energy > b.capacity_kwh * b.minimum_soc:
        discharge = min(
            max(0.0, requested - solar_load - grid_load),
            b.max_discharge_kw,
            max(0.0, inverter_kw - solar_load),
        )
    served = solar_load + grid_load + discharge
    critical_served = min(critical_demand, served)
    noncritical_served = min(noncritical, max(0.0, served - critical_served))
    solar_charge = grid_charge = 0.0
    if discharge == 0.0 and energy < b.capacity_kwh * b.maximum_soc:
        solar_charge = min(max(0.0, pv_kw - solar_load), b.max_charge_kw)
        if s.grid.charge_battery:
            grid_charge = min(
                max(0.0, grid_limit - grid_load),
                max(0.0, b.max_charge_kw - solar_charge),
                max(0.0, inverter_kw - solar_load - solar_charge),
            )
    return Dispatch(
        grid=grid_load + grid_charge,
        solar=solar_load + solar_charge,
        charge=solar_charge + grid_charge,
        discharge=discharge,
        grid_charge=grid_charge,
        critical=critical_served,
        noncritical=noncritical_served,
    )


def idealized_autonomy(s: SimulationRequest) -> float | None:
    """Analytic reference only when its constant, battery-only assumptions hold.

    Observed survival is computed exclusively from trace shortfalls. This
    independent formula may exceed the simulated horizon and is labelled so.
    """
    all_outage = not any(s.grid.profile_online) if s.grid.profile_online is not None else not s.grid.online
    all_dark = not any(s.solar.profile_kw) if s.solar.profile_kw is not None else s.solar.generation_kw == 0
    critical = s.load.critical_kw
    if (
        not all_outage
        or not all_dark
        or s.load.critical_profile_kw is not None
        or s.load.noncritical_profile_kw is not None
        or not s.inverter.islanding_capable
        or critical == 0
        or min(s.battery.max_discharge_kw, s.inverter.max_kw) < critical
        or (s.load.noncritical_kw > 0 and not s.load.shed_noncritical_during_outage)
    ):
        return None
    return round(
        s.battery.capacity_kwh
        * (s.battery.initial_soc - s.battery.minimum_soc)
        * s.battery.discharge_efficiency
        / critical, 12
    )


def simulate(request: SimulationRequest) -> SimulationResult:
    # Revalidate Python callers too: model_copy/model_construct can bypass Pydantic validation.
    s = SimulationRequest.model_validate(request.model_dump())
    b = s.battery
    minimum = b.capacity_kwh * b.minimum_soc
    maximum = b.capacity_kwh * b.maximum_soc
    energy = initial_energy = b.capacity_kwh * b.initial_soc
    step = s.step_minutes / 60
    trace: list[SimulationTracePoint] = []
    first_failure: float | None = None

    for index in range(s.interval_count):
        t = index * step
        interval_end = min((index + 1) * step, s.duration_hours)
        grid_online = s.grid.profile_online[index] if s.grid.profile_online is not None else s.grid.online
        pv_available = s.solar.profile_kw[index] if s.solar.profile_kw is not None else s.solar.generation_kw
        critical_demand = s.load.critical_profile_kw[index] if s.load.critical_profile_kw is not None else s.load.critical_kw
        noncritical_demand = s.load.noncritical_profile_kw[index] if s.load.noncritical_profile_kw is not None else s.load.noncritical_kw

        while t < interval_end:
            p = dispatch(s, energy, grid_online, pv_available, critical_demand, noncritical_demand)
            rate = p.charge * b.charge_efficiency - p.discharge / b.discharge_efficiency
            remaining = interval_end - t
            dt = remaining
            boundary = None
            if rate < 0:
                hit = (energy - minimum) / -rate
                if hit <= dt:
                    dt, boundary = hit, minimum
            elif rate > 0:
                hit = (maximum - energy) / rate
                if hit <= dt:
                    dt, boundary = hit, maximum
            if dt <= 0:
                raise EnergyBalanceError("non-positive event interval")
            end = interval_end if dt == remaining else t + dt
            next_energy = energy + rate * dt if boundary is None else boundary
            loss = (p.charge * (1 - b.charge_efficiency) + p.discharge * (1 / b.discharge_efficiency - 1)) * dt
            ac_residual = (p.grid + p.solar + p.discharge - p.critical - p.noncritical - p.charge) * dt
            storage_residual = next_energy - energy - rate * dt
            balance = (p.grid + p.solar - p.critical - p.noncritical) * dt - (next_energy - energy) - loss
            residual = max(abs(ac_residual), abs(storage_residual), abs(balance))
            if residual > BALANCE_TOLERANCE_KWH or not minimum <= next_energy <= maximum:
                raise EnergyBalanceError("energy conservation or battery bound violated")
            unserved = max(0.0, critical_demand - p.critical)
            unserved_noncritical = max(0.0, noncritical_demand - p.noncritical)
            if unserved > POWER_TOLERANCE_KW:
                status = "critical_failure"
                if first_failure is None:
                    first_failure = t
            elif unserved_noncritical > POWER_TOLERANCE_KW:
                status = "degraded"
            else:
                status = "normal" if grid_online else "islanded"
            trace.append(
                SimulationTracePoint(
                    t_utc=utc_stamp(s.start_utc, t),
                    t_end_utc=utc_stamp(s.start_utc, end),
                    elapsed_hours=t,
                    duration_hours=dt,
                    grid_online=grid_online,
                    grid_kw=p.grid,
                    solar_kw=p.solar,
                    solar_available_kw=pv_available,
                    solar_curtailed_kw=max(0.0, pv_available - p.solar),
                    grid_charge_kw=p.grid_charge,
                    battery_charge_kw=p.charge,
                    battery_discharge_kw=p.discharge,
                    battery_soc=energy / b.capacity_kwh,
                    battery_soc_end=next_energy / b.capacity_kwh,
                    battery_energy_kwh=energy,
                    battery_energy_end_kwh=next_energy,
                    critical_demand_kw=critical_demand,
                    critical_served_kw=p.critical,
                    noncritical_demand_kw=noncritical_demand,
                    noncritical_served_kw=p.noncritical,
                    unserved_critical_kw=unserved,
                    unserved_noncritical_kw=unserved_noncritical,
                    conversion_loss_kwh=loss,
                    ac_balance_residual_kwh=ac_residual,
                    storage_balance_residual_kwh=storage_residual,
                    balance_residual_kwh=balance,
                    status=status,
                )
            )
            energy = next_energy
            t = end

    def integral(field: str) -> float:
        return fsum(getattr(point, field) * point.duration_hours for point in trace)

    served_critical = integral("critical_served_kw")
    total_critical = integral("critical_demand_kw")
    grid_energy = integral("grid_kw")
    solar_energy = integral("solar_kw")
    noncritical_energy = integral("noncritical_served_kw")
    total_loss = fsum(point.conversion_loss_kwh for point in trace)
    cumulative_balance = fsum([grid_energy, solar_energy, -served_critical, -noncritical_energy, initial_energy, -energy, -total_loss])
    if abs(cumulative_balance) > BALANCE_TOLERANCE_KWH:
        raise EnergyBalanceError("cumulative energy conservation violated")
    digest = hashlib.sha256(canonical_input(s).encode("utf-8")).hexdigest()
    warnings = ["Quasi-static energy model; not a field test or transient AC network model."]
    if not any(point.solar_available_kw for point in trace):
        warnings.append("Solar generation is zero; omitted generation defaults to zero (no inferred weather).")
    if any(not point.grid_online and point.solar_available_kw > 0 for point in trace) and not (
        s.inverter.islanding_capable and s.solar.islanding_capable
    ):
        warnings.append("PV is unavailable during outages without both islanding compatibility flags.")
    return SimulationResult(
        run_id=str(uuid5(NAMESPACE_URL, f"lastlight:{MODEL_VERSION}:{digest}")),
        input_hash=digest,
        seed=s.seed,
        input=s,
        provenance=s.provenance,
        warnings=warnings,
        trace=trace,
        summary=SimulationSummary(
            critical_survival_hours=round(first_failure, 12) if first_failure is not None else None,
            first_failure_utc=utc_stamp(s.start_utc, first_failure) if first_failure is not None else None,
            served_critical_fraction=served_critical / total_critical if total_critical else 1.0,
            unserved_critical_kwh=integral("unserved_critical_kw"),
            max_balance_residual_kwh=max(
                max(abs(p.balance_residual_kwh), abs(p.ac_balance_residual_kwh), abs(p.storage_balance_residual_kwh)) for p in trace
            ),
            observed_duration_hours=s.duration_hours,
            survived_full_window=first_failure is None,
            idealized_autonomy_hours=idealized_autonomy(s),
            total_critical_demand_kwh=total_critical,
            served_critical_kwh=served_critical,
            served_noncritical_kwh=noncritical_energy,
            unserved_noncritical_kwh=integral("unserved_noncritical_kw"),
            grid_import_kwh=grid_energy,
            solar_available_kwh=integral("solar_available_kw"),
            solar_used_kwh=solar_energy,
            solar_curtailed_kwh=integral("solar_curtailed_kw"),
            battery_charge_kwh=integral("battery_charge_kw"),
            battery_discharge_kwh=integral("battery_discharge_kw"),
            conversion_loss_kwh=total_loss,
            initial_battery_energy_kwh=initial_energy,
            final_battery_energy_kwh=energy,
            usable_capacity_kwh=maximum - minimum,
            ending_soc=energy / b.capacity_kwh,
            cumulative_balance_residual_kwh=cumulative_balance,
        ),
    )


def compare(request: ComparisonRequest) -> ComparisonResult:
    request = ComparisonRequest.model_validate(request.model_dump())
    upgraded_input = request.baseline.model_dump()
    if request.upgrade == "battery_36_kwh":
        upgraded_input["battery"]["capacity_kwh"] = 36.0
    else:
        upgraded_input["battery"]["initial_soc"] = 1.0
    baseline = simulate(request.baseline)
    upgraded = simulate(SimulationRequest.model_validate(upgraded_input))

    def difference(name: str) -> float | None:
        before, after = getattr(baseline.summary, name), getattr(upgraded.summary, name)
        return after - before if before is not None and after is not None else None

    return ComparisonResult(
        upgrade=request.upgrade,
        baseline=baseline,
        upgraded=upgraded,
        delta=ComparisonDelta(
            served_critical_kwh=upgraded.summary.served_critical_kwh - baseline.summary.served_critical_kwh,
            unserved_critical_kwh=upgraded.summary.unserved_critical_kwh - baseline.summary.unserved_critical_kwh,
            critical_survival_hours=difference("critical_survival_hours"),
            idealized_autonomy_hours=difference("idealized_autonomy_hours"),
        ),
    )
