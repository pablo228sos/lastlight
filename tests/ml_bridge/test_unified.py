"""Tests must reach the actual official app, not only a standalone ML router."""

import shutil

import pytest
from fastapi.testclient import TestClient

from ml_bridge.adapter import DEFAULT_CHECKPOINT
from services.simulation.api import app


@pytest.mark.parametrize("step", [1, 15, 60])
@pytest.mark.parametrize("horizon", [9.119, 9.12, 9.120001, 16.0])
def test_unified_http_keeps_exact_physics_and_real_neural(step, horizon):
    with TestClient(app) as client:
        scenario = {"duration_hours": horizon, "step_minutes": step}
        physical = client.post("/api/v1/simulations", json=scenario)
        response = client.post(
            "/api/v1/ml/fragility/assess", json={"scenario": scenario}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["physics"] == physical.json()
        assert body["physics"]["summary"]["survived_full_window"] == (horizon <= 9.12)
        assert body["neural"]["status"] == "available"
        assert body["neural"]["model_version"] == "fragility-official-v1-8b40929366e6"
        assert body["physics_authoritative"] is True


@pytest.mark.parametrize("corrupt", [False, True])
def test_unified_missing_or_corrupt_model_preserves_physics(
    tmp_path, monkeypatch, corrupt
):
    if corrupt:
        shutil.copytree(DEFAULT_CHECKPOINT, tmp_path, dirs_exist_ok=True)
        (tmp_path / "model.pt").write_bytes(b"invalid checkpoint")
    monkeypatch.setattr(app.state, "fragility_checkpoint_dir", tmp_path, raising=False)
    with TestClient(app) as client:
        response = client.post("/api/v1/ml/fragility/assess", json={"scenario": {}})
        assert response.status_code == 200
        body = response.json()
        assert body["neural"]["status"] != "available"
        assert body["neural"]["warnings"]
        assert body["physics"] == client.post("/api/v1/simulations", json={}).json()
        assert (
            client.post(
                "/api/v1/frontiers", json={"soc_points": 3, "duration_points": 3}
            ).status_code
            == 200
        )


def test_unified_validates_identity_and_has_additive_contract():
    with TestClient(app) as client:
        assert (
            client.post(
                "/api/v1/ml/fragility/assess",
                json={"scenario": {}, "schema_version": "1.1.0"},
            ).status_code
            == 422
        )
        doc = client.get("/api/v1/intelligence/openapi.json")
        assert doc.status_code == 200
        assert "/api/v1/ml/fragility/assess" in doc.json()["paths"]
        assert "/api/v1/simulations" in doc.json()["paths"]


def test_changed_checkpoint_invalidates_a_previously_warm_cache(tmp_path, monkeypatch):
    shutil.copytree(DEFAULT_CHECKPOINT, tmp_path, dirs_exist_ok=True)
    monkeypatch.setattr(app.state, "fragility_checkpoint_dir", tmp_path, raising=False)
    with TestClient(app) as client:
        first = client.post("/api/v1/ml/fragility/assess", json={"scenario": {}}).json()
        assert first["neural"]["status"] == "available"
        (tmp_path / "model.pt").write_bytes(b"corrupted after warm inference")
        second = client.post(
            "/api/v1/ml/fragility/assess", json={"scenario": {}}
        ).json()
        assert second["neural"]["status"] == "incompatible_checkpoint"
        assert second["physics"] == first["physics"]
