import pytest
from fastapi.testclient import TestClient

from services.simulation.api import app
from services.simulation.schemas import SimulationRequest
from ml.frontier import physics_frontier


def test_physics_frontier_matches_known_boundary():
    result = physics_frontier(
        SimulationRequest(duration_hours=24),
        soc_points=5,
        duration_points=9,
        maximum_hours=24,
    )
    assert len(result["trace"]) == 45
    for cell in result["trace"]:
        autonomy = max(0, (cell["initial_soc"] - 0.2) * 24 * 0.95 / 1.5)
        assert cell["failed"] == (cell["duration_hours"] > autonomy + 1e-9)
        assert cell["physics_verified"] is True
    assert result["summary"]["physics_calls"] == 5


def test_api_prediction_always_includes_physics():
    with TestClient(app) as client:
        response = client.post("/api/v1/fragility/predict", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["critical_survival_hours"] == pytest.approx(9.12)
        assert data["engineering_clearance"] is False
        assert data["physics_version"]
        assert data["trace"] and data["physics_verified"]
        assert (
            client.post(
                "/api/v1/fragility/frontier", json={"soc_points": 10000}
            ).status_code
            == 422
        )
        frontier = client.post(
            "/api/v1/fragility/frontier",
            json={"soc_points": 3, "duration_points": 3, "include_ml": True},
        )
        assert frontier.status_code == 200, frontier.text
        assert len(frontier.json()["verified_candidates"]) == 9


def test_frontier_rejects_profile_extrapolation():
    scenario = SimulationRequest.model_validate(
        {"duration_hours": 1, "solar": {"profile_kw": [0, 0, 0, 0]}}
    )
    with pytest.raises(ValueError):
        physics_frontier(scenario, maximum_hours=24)
