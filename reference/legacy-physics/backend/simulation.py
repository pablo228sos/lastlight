"""Deterministic, single-bus critical-load energy resilience simulator.

All power values are AC-side kW; battery capacity is internal DC kWh.
15-minute quasi-static steps, no voltage/transient/power-flow physics.
No connection to real electrical equipment. Research/demo only.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from math import sin, pi
from typing import Literal


@dataclass(frozen=True)
class Scenario:
    name: str = "Bishkek School / Winter Evening"
    duration_hours: float = 16.0
    start_hour: float = 18.0
    step_minutes: int = 15
    capacity_kwh: float = 24.0
    initial_soc: float = 80.0
    minimum_soc: float = 20.0
    critical_load_kw: float = 1.5
    noncritical_load_kw: float = 2.0
    max_discharge_kw: float = 8.0
    max_charge_kw: float = 6.0
    inverter_max_kw: float = 8.0
    discharge_efficiency: float = 0.95
    charge_efficiency: float = 0.95
    pv_peak_kw: float = 0.0
    sky_condition: Literal['winter_clear', 'winter_cloudy', 'no_solar'] = 'no_solar'
    islanding_capable: bool = True
    shed_noncritical: bool = True


def validate(s: Scenario) -> None:
    if not 0.25 <= s.duration_hours <= 48: raise ValueError('duration_hours must be 0.25..48')
    if s.step_minutes not in (15, 60): raise ValueError('step_minutes must be 15 or 60')
    if abs(s.duration_hours * 60 / s.step_minutes - round(s.duration_hours * 60 / s.step_minutes)) > 1e-8:
        raise ValueError('duration must be multiple of step_minutes')
    if not 0 <= s.start_hour < 24: raise ValueError('start_hour must be 0..24')
    if not 0 <= s.minimum_soc < s.initial_soc <= 100: raise ValueError('SOC must satisfy 0 <= min < initial <= 100')
    if not 0 < s.capacity_kwh <= 20000: raise ValueError('capacity_kwh invalid')
    for key in ['critical_load_kw','noncritical_load_kw','max_discharge_kw','max_charge_kw','inverter_max_kw','pv_peak_kw']:
        if not 0 <= getattr(s,key) <= 50000: raise ValueError(f'{key} invalid')
    if s.critical_load_kw <= 0: raise ValueError('critical_load_kw must be positive')
    if not 0 < s.discharge_efficiency <= 1 or not 0 < s.charge_efficiency <= 1:
        raise ValueError('efficiencies must be (0,1]')


def pv_ac_available_kw(s: Scenario, t_hours: float) -> float:
    """Synthetic smooth *illustrative* winter PV profile; NOT historical weather."""
    if not s.islanding_capable or s.sky_condition == 'no_solar': return 0.0
    hour = (s.start_hour + t_hours) % 24
    if not 8.5 < hour < 17.5: return 0.0
    profile = sin(pi * (hour - 8.5) / 9.0)
    factor = 0.78 if s.sky_condition == 'winter_clear' else 0.28
    return max(0.0, s.pv_peak_kw * profile * factor)


def run(s: Scenario) -> dict:
    validate(s)
    dt = s.step_minutes / 60.0
    n = round(s.duration_hours / dt)
    min_energy = s.capacity_kwh * s.minimum_soc / 100
    energy = s.capacity_kwh * s.initial_soc / 100
    unmet_kwh = 0.0
    served_critical_kwh = 0.0
    pv_generated_kwh = 0.0
    pv_used_kwh = 0.0
    first_failure = None
    trace = []

    def snap(t:float, p_pv:float, p_bat:float, p_charge:float, served_crit:float, served_noncrit:float, unmet:float) -> dict:
        soc = round(energy / s.capacity_kwh * 100, 5)
        return {
            't_hours': round(t, 5), 'local_hour': round((s.start_hour+t)%24,5),
            'soc_pct': soc, 'battery_energy_kwh': round(energy, 6),
            'pv_used_kw': round(p_pv, 6), 'battery_discharge_kw': round(p_bat, 6),
            'battery_charge_kw': round(p_charge, 6),
            'critical_served_kw': round(served_crit, 6),
            'noncritical_served_kw': round(served_noncrit, 6),
            'unserved_critical_kw': round(unmet, 6),
            'critical_online': unmet < 1e-9,
            'grid_online': False
        }

    trace.append(snap(0, 0, 0, 0, s.critical_load_kw, 0, 0))
    for i in range(n):
        t = i * dt
        available_pv = min(pv_ac_available_kw(s, t + dt/2), s.inverter_max_kw)
        pv_generated_kwh += available_pv * dt
        noncritical_requested = 0 if s.shed_noncritical else s.noncritical_load_kw
        total_requested = s.critical_load_kw + noncritical_requested
        pv_to_critical = min(available_pv, s.critical_load_kw)
        pv_remainder = available_pv - pv_to_critical
        pv_to_noncritical = min(pv_remainder, noncritical_requested)
        remaining_critical = s.critical_load_kw - pv_to_critical
        remaining_noncritical = noncritical_requested - pv_to_noncritical

        ac_power_limit = max(0., min(s.max_discharge_kw, s.inverter_max_kw-available_pv))
        available_battery_ac_kw = min(ac_power_limit, max(0, energy-min_energy) * s.discharge_efficiency/dt)
        discharge_critical_kw = min(remaining_critical, available_battery_ac_kw)
        discharge_noncritical_kw = min(remaining_noncritical, available_battery_ac_kw - discharge_critical_kw)
        discharge_kw = discharge_critical_kw + discharge_noncritical_kw
        energy -= discharge_kw * dt / s.discharge_efficiency
        energy = max(min_energy, energy)

        served_critical = pv_to_critical + discharge_critical_kw
        unserved_critical = max(0.0,s.critical_load_kw-served_critical)
        served_noncritical = pv_to_noncritical + discharge_noncritical_kw
        pv_used = pv_to_critical+pv_to_noncritical
        pv_left = available_pv - pv_used
        charge_kw = min(pv_left, s.max_charge_kw, max(0,(s.capacity_kwh-energy)/(dt*s.charge_efficiency)))
        energy += charge_kw*dt*s.charge_efficiency
        pv_used += charge_kw
        energy = min(s.capacity_kwh, energy)
        unmet_kwh += unserved_critical*dt
        served_critical_kwh += served_critical*dt
        pv_used_kwh += pv_used*dt

        if unserved_critical > 1e-9 and first_failure is None:
            # If shortfall is purely power-limited, failure starts at beginning of step;
            # if energy-limited, estimate time of cell depletion within step.
            if ac_power_limit + pv_to_critical < s.critical_load_kw - 1e-9:
                first_failure = t
            elif remaining_critical > 1e-9:
                # start-of-step battery energy obtained from ending energy and discharge.
                energy_at_start = energy + discharge_kw * dt / s.discharge_efficiency - charge_kw*dt*s.charge_efficiency
                useful_ac_critical = max(0, energy_at_start - min_energy)*s.discharge_efficiency
                # because critical gets dispatch priority, noncritical battery use is zero when critical short.
                first_failure = t + min(dt, useful_ac_critical/remaining_critical)
            else:
                first_failure = t

        trace.append(snap((i+1)*dt, pv_used, discharge_kw, charge_kw,
                          served_critical,served_noncritical,unserved_critical))

    # Note: an outage with no critical shortfall lasts beyond the inspected horizon.
    return {
        'scenario': asdict(s),
        'summary': {
            'critical_load_coverage_pct': round(100*served_critical_kwh/(s.critical_load_kw*s.duration_hours), 3),
            'unserved_critical_energy_kwh': round(unmet_kwh, 6),
            'first_failure_hours': round(first_failure, 4) if first_failure is not None else None,
            'survived_full_window': first_failure is None,
            'ending_soc_pct': round(energy/s.capacity_kwh*100, 4),
            'pv_generated_kwh': round(pv_generated_kwh, 4),
            'pv_used_kwh': round(pv_used_kwh, 4),
            'total_critical_demand_kwh': round(s.critical_load_kw*s.duration_hours,4),
            'served_critical_energy_kwh': round(served_critical_kwh, 6),
        },
        'trace': trace,
        'provenance': {
            'load': 'SYNTHETIC_USER_CONFIGURED',
            'weather': 'SYNTHETIC_DAYLIGHT_PROFILE',
            'physical_model': 'SINGLE_BUS_BALANCE_V1',
            'timebase': '15_MIN_STEP' if s.step_minutes == 15 else '60_MIN_STEP',
            'limitations': 'Research simulation only; no measured building load, real outage prediction, or transient AC network modeling.'
        }
    }
