from fastapi.testclient import TestClient
from services.simulation.api import app


def test_historical_forecast_is_a_reproducible_labelled_estimate():
    with TestClient(app) as client:
        body = {"mode": "historical", "history_kw": [2] * 168, "hours": 24}
        a = client.post("/api/v1/forecast/load", json=body)
        b = client.post("/api/v1/forecast/load", json=body)
        assert a.status_code == 200
        assert a.json() == b.json()
        assert all(p["demand_kw"] == 2 for p in a.json()["trace"])
        assert a.json()["summary"]["neural_model"] is False
        assert a.json()["provenance"]["category"] == "research_derived"
        assert (
            client.post(
                "/api/v1/forecast/load", json={"mode": "historical"}
            ).status_code
            == 422
        )


def test_research_cold_start_uses_versioned_training_profile():
    with TestClient(app) as client:
        body = {'mode':'cold_start','primary_use':'Education','local_timezone':'Asia/Bishkek'}
        first = client.post('/api/v1/forecast/load', json=body)
        second = client.post('/api/v1/forecast/load', json=body)
    assert first.status_code == 200
    assert first.json() == second.json()
    assert len(first.json()['trace']) == 24
    assert first.json()['physics_version'] is None
    assert all(point['demand_kw'] >= 0 for point in first.json()['trace'])
        assert (
            client.post(
                "/api/v1/forecast/load",
                json={"mode": "cold_start", "local_timezone": "invalid/zone"},
            ).status_code
            == 422
        )
