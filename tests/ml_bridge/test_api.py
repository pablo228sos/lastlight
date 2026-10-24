from fastapi import FastAPI
from fastapi.testclient import TestClient

from ml_bridge.api import create_router
from services.simulation.engine import simulate
from services.simulation.frontier import scenario_at
from services.simulation.schemas import SimulationRequest


def client(directory=None):
    app = FastAPI()
    app.include_router(create_router(directory))
    return TestClient(app)


def test_real_http_assessment_preserves_official_result():
    response = client().post(
        "/api/v1/ml/fragility/assess", json={"scenario": {"duration_hours": 16}}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["physics"] == simulate(SimulationRequest(duration_hours=16)).model_dump(
        mode="json"
    )
    assert body["neural"]["status"] == "available"
    assert body["neural"]["model_version"] != body["physics"]["model_version"]
    assert body["physics_authoritative"] is True


def test_http_model_absence_keeps_physics_and_version_errors_are_explicit(tmp_path):
    response = client(tmp_path).post(
        "/api/v1/ml/fragility/assess", json={"scenario": {"duration_hours": 9.12}}
    )
    assert response.status_code == 200
    assert response.json()["physics"]["summary"]["survived_full_window"] is True
    assert response.json()["neural"]["status"] == "unavailable"
    assert (
        client()
        .post(
            "/api/v1/ml/fragility/assess",
            json={"scenario": {}, "schema_version": "1.1.0"},
        )
        .status_code
        == 422
    )


def test_selected_candidates_are_independently_officially_verified():
    points = [
        {"initial_soc": 0.8, "duration_hours": h} for h in [9.119, 9.12, 9.120001]
    ]
    response = client().post(
        "/api/v1/ml/fragility/candidates",
        json={"scenario": {"duration_hours": 16}, "points": points, "limit": 3},
    )
    assert response.status_code == 200
    result = response.json()
    assert len(result["candidates"]) == 3
    for cell in result["candidates"]:
        actual = simulate(
            scenario_at(
                SimulationRequest(duration_hours=16),
                cell["initial_soc"],
                cell["duration_hours"],
            )
        )
        assert cell["physics_summary"] == actual.summary.model_dump(mode="json")
        assert cell["physics_run_id"] == actual.run_id
        assert cell["physics_verified"] is True
        assert cell["physics_model_version"] == "lastlight-dispatch-1.0.0"


def test_candidate_budget_and_profile_extrapolation_are_rejected():
    http = client()
    assert (
        http.post(
            "/api/v1/ml/fragility/candidates",
            json={
                "scenario": {},
                "points": [{"initial_soc": 0.8, "duration_hours": 12}] * 1601,
            },
        ).status_code
        == 422
    )
    assert (
        http.post(
            "/api/v1/ml/fragility/candidates",
            json={
                "scenario": {"duration_hours": 1, "solar": {"profile_kw": [0.0] * 4}},
                "points": [{"initial_soc": 0.8, "duration_hours": 2}],
            },
        ).status_code
        == 422
    )
