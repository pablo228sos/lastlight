"""Input-only timing/energy summaries; deliberately no simulator import."""

from math import ceil
import numpy as np

from ml_bridge.features import FEATURE_NAMES, features

NAMES = FEATURE_NAMES + [
    "initial_useful_ac_kwh",
    "first_restoration_hours",
    "critical_energy_before_restoration",
    "islanded_usable_pv_kwh",
    "critical_deficit_kwh",
    "requested_deficit_kwh",
    "max_islanded_block_deficit_kwh",
    "initial_energy_minus_critical_deficit",
    "peak_critical_power_shortfall_kw",
    "peak_requested_power_shortfall_kw",
    "first_half_supply_kwh",
    "last_half_supply_kwh",
    "grid_offline_hours",
    "critical_energy_before_restoration_minus_initial",
    "islanded_critical_energy_kwh",
]


def timing_features(s):
    n = ceil(s.duration_hours * 60 / s.step_minutes)
    durations = np.minimum(
        s.step_minutes / 60, s.duration_hours - np.arange(n) * s.step_minutes / 60
    )
    grid = np.array(
        s.grid.profile_online
        if s.grid.profile_online is not None
        else [s.grid.online] * n
    )
    pv = np.array(
        s.solar.profile_kw
        if s.solar.profile_kw is not None
        else [s.solar.generation_kw] * n
    )
    inverter = np.where(grid | s.inverter.islanding_capable, s.inverter.max_kw, 0.0)
    pv = np.where(
        grid | (s.solar.islanding_capable and s.inverter.islanding_capable),
        np.minimum(pv, inverter),
        0.0,
    )
    supply = pv + np.where(grid, s.grid.import_limit_kw, 0.0)
    requested = s.load.critical_kw + np.where(
        ~grid & s.load.shed_noncritical_during_outage, 0.0, s.load.noncritical_kw
    )
    critical_deficit = np.maximum(0.0, s.load.critical_kw - supply) * durations
    requested_deficit = np.maximum(0.0, requested - supply) * durations
    battery_limit = np.minimum(
        s.battery.max_discharge_kw, np.maximum(0.0, inverter - pv)
    )
    initial = (
        s.battery.capacity_kwh
        * (s.battery.initial_soc - s.battery.minimum_soc)
        * s.battery.discharge_efficiency
    )
    first_restore = (
        float(durations[: np.flatnonzero(grid)[0]].sum())
        if grid.any()
        else s.duration_hours
    )
    blocks, block = [], 0.0
    for offline, deficit in zip(~grid, critical_deficit, strict=True):
        if offline:
            block += deficit
        else:
            blocks.append(block)
            block = 0.0
    blocks.append(block)
    midpoint = n // 2
    added = [
        initial,
        first_restore,
        s.load.critical_kw * first_restore,
        float((pv * durations * ~grid).sum()),
        float(critical_deficit.sum()),
        float(requested_deficit.sum()),
        max(blocks),
        initial - float(critical_deficit.sum()),
        float(np.maximum(0.0, s.load.critical_kw - supply - battery_limit).max()),
        float(np.maximum(0.0, requested - supply - battery_limit).max()),
        float((supply * durations)[:midpoint].sum()),
        float((supply * durations)[midpoint:].sum()),
        float(durations[~grid].sum()),
        s.load.critical_kw * first_restore - initial,
        s.load.critical_kw * float(durations[~grid].sum()),
    ]
    result = np.array([*features(s), *added], dtype=float)
    if result.shape != (len(NAMES),) or not np.isfinite(result).all():
        raise ValueError("Invalid input timing features")
    return result
