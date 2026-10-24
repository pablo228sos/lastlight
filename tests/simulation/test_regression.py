import pytest
from fastapi.testclient import TestClient

from services.simulation.api import app
from services.simulation.engine import simulate
from services.simulation.schemas import SimulationRequest


@pytest.mark.parametrize("capacity,soc,expected", [(24, 0.8, 9.12), (36, 0.8, 13.68), (24, 1.0, 12.16)])
@pytest.mark.parametrize("step", [1, 15, 60])
def test_analytic_autonomy(capacity, soc, expected, step):
    request = SimulationRequest.model_validate({
        "duration_hours": 16, "step_minutes": step,
        "battery": {"capacity_kwh": capacity, "initial_soc": soc},
    })
    result = simulate(request)
    assert result.summary.critical_survival_hours == pytest.approx(expected, abs=1e-10)
    assert result.summary.idealized_autonomy_hours == pytest.approx(expected)
    assert result.summary.unserved_critical_kwh == pytest.approx((16 - expected) * 1.5)
    assert result.summary.ending_soc == pytest.approx(0.2)
    first = next(p for p in result.trace if p.unserved_critical_kw > 1e-9)
    assert first.elapsed_hours == pytest.approx(expected)
    assert first.t_utc == result.summary.first_failure_utc


def test_default_api_is_reproducible():
    with TestClient(app) as client:
        a = client.post("/api/v1/simulations", json={})
        b = client.post("/api/v1/simulations", json={})
    assert a.status_code == 200
    assert a.json() == b.json()
    assert a.json()["summary"]["critical_survival_hours"] == pytest.approx(9.12)
