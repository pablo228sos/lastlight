"""Independent reference equations, imported only inside tests (never production)."""

import importlib.util
import sys
from pathlib import Path

import pytest

from services.simulation.engine import simulate
from services.simulation.schemas import SimulationRequest


@pytest.fixture(scope="module")
def legacy():
    path = (
        Path(__file__).resolve().parents[2]
        / "reference/legacy-physics/backend/simulation.py"
    )
    spec = importlib.util.spec_from_file_location("lastlight_legacy_reference", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "capacity,soc,eta,load",
    [
        (24, 0.8, 0.95, 1.5),
        (36, 0.8, 0.95, 1.5),
        (24, 1.0, 0.95, 1.5),
        (12.34, 0.67, 0.83, 1.17),
    ],
)
@pytest.mark.parametrize("step", [15, 60])
def test_independent_legacy_constant_battery_only_equations(
    legacy, capacity, soc, eta, load, step
):
    reference = legacy.run(
        legacy.Scenario(
            duration_hours=16,
            step_minutes=step,
            capacity_kwh=capacity,
            initial_soc=soc * 100,
            discharge_efficiency=eta,
            critical_load_kw=load,
        )
    )
    official = simulate(
        SimulationRequest.model_validate(
            {
                "duration_hours": 16,
                "step_minutes": step,
                "battery": {
                    "capacity_kwh": capacity,
                    "initial_soc": soc,
                    "discharge_efficiency": eta,
                },
                "load": {"critical_kw": load},
            }
        )
    )
    assert official.summary.critical_survival_hours == pytest.approx(
        reference["summary"]["first_failure_hours"], abs=1e-4
    )
    assert official.summary.served_critical_kwh == pytest.approx(
        reference["summary"]["served_critical_energy_kwh"], abs=1e-6
    )
    assert official.summary.unserved_critical_kwh == pytest.approx(
        reference["summary"]["unserved_critical_energy_kwh"], abs=1e-6
    )
    assert official.summary.ending_soc * 100 == pytest.approx(
        reference["summary"]["ending_soc_pct"], abs=1e-4
    )
