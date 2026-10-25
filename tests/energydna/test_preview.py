from fastapi.testclient import TestClient

from services.simulation.api import app


def test_packaged_historical_preview_runs_real_gru_and_persistence():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/ml/energydna/forecast", json={"example_id": "rat-march20"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["neural_status"] == "available"
        assert body["model_version"] == "energydna-gru-v1-56d366ec3532"
        assert body["horizon_hours"] == 1
        assert body["preferred_method"] == "persistence"
        assert body["baseline_kw"] == body["history_kw"][-1]
        assert body["neural_kw"] >= 0 and body["recorded_actual_kw"] >= 0
        assert body["connected_to_physics"] is False
        assert len(body["history_kw"]) == 168
        assert (
            client.post(
                "/api/v1/ml/energydna/forecast", json={"example_id": "unknown"}
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/v1/ml/energydna/forecast",
                content='{"example_id":"rat-march20","history_kw":[NaN]}',
                headers={"Content-Type": "application/json"},
            ).status_code
            == 422
        )


def test_missing_forecast_model_retains_baseline_and_physics(tmp_path, monkeypatch):
    monkeypatch.setattr(app.state, "energydna_checkpoint_dir", tmp_path, raising=False)
    with TestClient(app) as client:
        body = client.post(
            "/api/v1/ml/energydna/forecast", json={"example_id": "rat-march20"}
        ).json()
        assert body["neural_status"] == "unavailable"
        assert body["neural_kw"] is None
        assert body["baseline_kw"] == body["history_kw"][-1]
        assert client.post("/api/v1/simulations", json={}).status_code == 200


def test_changed_historical_data_is_not_presented_as_a_verified_example(
    tmp_path, monkeypatch
):
    from ml_bridge import forecast

    bad = tmp_path / "historical.json"
    bad.write_text("{}", encoding="utf8")
    monkeypatch.setattr(forecast, "EXAMPLES", bad)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/ml/energydna/forecast", json={"example_id": "rat-march20"}
        )
        assert response.status_code == 503
        assert "checksum" in response.json()["error"]["message"]
        assert client.post("/api/v1/simulations", json={}).status_code == 200
