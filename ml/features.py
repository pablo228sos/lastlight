"""Input-only features. No simulation outcome is used as a predictor."""

import numpy as np

from services.simulation.schemas import SimulationRequest

FEATURE_VERSION = "input-statistics-1"
FEATURE_NAMES = [
    "capacity_kwh",
    "usable_initial_kwh",
    "initial_soc",
    "minimum_soc",
    "maximum_soc",
    "charge_efficiency",
    "discharge_efficiency",
    "max_charge_kw",
    "max_discharge_kw",
    "inverter_kw",
    "critical_mean_kw",
    "critical_peak_kw",
    "critical_std_kw",
    "noncritical_mean_kw",
    "noncritical_peak_kw",
    "solar_mean_kw",
    "solar_peak_kw",
    "solar_std_kw",
    "duration_hours",
    "grid_online_fraction",
    "inverter_islanding",
    "solar_islanding",
    "shed_noncritical",
    "start_hour_sin",
    "start_hour_cos",
    "early_critical_mean_kw",
    "early_solar_mean_kw",
]


def features(s: SimulationRequest) -> np.ndarray:
    n = s.interval_count
    critical = np.asarray(
        s.load.critical_profile_kw
        if s.load.critical_profile_kw is not None
        else [s.load.critical_kw] * n
    )
    noncritical = np.asarray(
        s.load.noncritical_profile_kw
        if s.load.noncritical_profile_kw is not None
        else [s.load.noncritical_kw] * n
    )
    solar = np.asarray(
        s.solar.profile_kw
        if s.solar.profile_kw is not None
        else [s.solar.generation_kw] * n
    )
    grid = np.asarray(
        s.grid.profile_online
        if s.grid.profile_online is not None
        else [s.grid.online] * n
    )
    b = s.battery
    angle = (s.start_utc.hour + s.start_utc.minute / 60) * 2 * np.pi / 24
    early = max(1, n // 4)
    return np.array(
        [
            b.capacity_kwh,
            b.capacity_kwh * (b.initial_soc - b.minimum_soc),
            b.initial_soc,
            b.minimum_soc,
            b.maximum_soc,
            b.charge_efficiency,
            b.discharge_efficiency,
            b.max_charge_kw,
            b.max_discharge_kw,
            s.inverter.max_kw,
            critical.mean(),
            critical.max(),
            critical.std(),
            noncritical.mean(),
            noncritical.max(),
            solar.mean(),
            solar.max(),
            solar.std(),
            s.duration_hours,
            grid.mean(),
            float(s.inverter.islanding_capable),
            float(s.solar.islanding_capable),
            float(s.load.shed_noncritical_during_outage),
            np.sin(angle),
            np.cos(angle),
            critical[:early].mean(),
            solar[:early].mean(),
        ],
        dtype=np.float64,
    )
