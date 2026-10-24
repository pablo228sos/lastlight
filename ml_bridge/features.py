"""Official-v1 inputs only. No dispatch result or failure label is a feature."""

import hashlib
import json
import ast
from pathlib import Path
from math import cos, pi, sin
from statistics import fmean, pstdev

from services.simulation.schemas import SimulationRequest

FEATURE_SCHEMA = "lastlight-official-v1-features-1"
FEATURE_NAMES = [
    "capacity_kwh",
    "initial_usable_kwh",
    "initial_soc",
    "minimum_soc",
    "maximum_soc",
    "charge_efficiency",
    "discharge_efficiency",
    "max_charge_kw",
    "max_discharge_kw",
    "inverter_kw",
    "critical_kw",
    "noncritical_kw",
    "duration_hours",
    "step_minutes",
    "solar_mean_kw",
    "solar_peak_kw",
    "solar_std_kw",
    "solar_early_mean_kw",
    "grid_online_fraction",
    "grid_early_online_fraction",
    "longest_outage_hours",
    "grid_import_limit_kw",
    "inverter_islanding",
    "solar_islanding",
    "shed_noncritical",
    "grid_charge_battery",
    "start_hour_sin",
    "start_hour_cos",
]
FEATURE_SHA256 = hashlib.sha256(
    json.dumps(
        {"schema": FEATURE_SCHEMA, "names": FEATURE_NAMES}, sort_keys=True
    ).encode()
).hexdigest()


def feature_source_sha256() -> str:
    def canonical(node):
        if node is Ellipsis:
            return {"constant": "Ellipsis"}
        if isinstance(node, ast.AST):
            return {
                "node": type(node).__name__,
                "fields": {
                    key: canonical(value) for key, value in ast.iter_fields(node)
                },
            }
        if isinstance(node, list):
            return [canonical(value) for value in node]
        return node

    # Explicit fields avoid Python-version changes in ast.dump's empty-field formatting.
    syntax = json.dumps(
        canonical(ast.parse(Path(__file__).read_text(encoding="utf-8"))),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(syntax.encode()).hexdigest()


def features(scenario: SimulationRequest) -> tuple[float, ...]:
    s = SimulationRequest.model_validate(scenario.model_dump())
    n = s.interval_count
    pv = (
        s.solar.profile_kw
        if s.solar.profile_kw is not None
        else [s.solar.generation_kw] * n
    )
    grid = (
        s.grid.profile_online
        if s.grid.profile_online is not None
        else [s.grid.online] * n
    )
    early = max(1, n // 4)
    longest = current = 0.0
    for i, online in enumerate(grid):
        dt = min(s.step_minutes / 60, s.duration_hours - i * s.step_minutes / 60)
        current = 0.0 if online else current + dt
        longest = max(longest, current)
    angle = (s.start_utc.hour + s.start_utc.minute / 60) * 2 * pi / 24
    b = s.battery
    return tuple(
        float(value)
        for value in [
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
            s.load.critical_kw,
            s.load.noncritical_kw,
            s.duration_hours,
            s.step_minutes,
            fmean(pv),
            max(pv),
            pstdev(pv),
            fmean(pv[:early]),
            fmean(grid),
            fmean(grid[:early]),
            longest,
            s.grid.import_limit_kw,
            s.inverter.islanding_capable,
            s.solar.islanding_capable,
            s.load.shed_noncritical_during_outage,
            s.grid.charge_battery,
            sin(angle),
            cos(angle),
        ]
    )
