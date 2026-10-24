"""Selective PR #7 frontier integration against the official v1 engine."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from services.simulation.api import app
from services.simulation.engine import simulate
from services.simulation.frontier import (
    FrontierRequest,
    observed_before_horizon,
    physics_frontier,
    scenario_at,
)
from services.simulation.schemas import SimulationRequest


def test_frontier_cells_agree_with_independent_official_runs():
    request = FrontierRequest(soc_points=5, duration_points=5, maximum_hours=12)
    result = physics_frontier(request)
    assert result["summary"] == {
        "physics_calls": 5,
        "verified_cells": 25,
        "method": "one official physics trace per SOC column; exclusive horizon classification",
    }
    assert result["physics_version"] == "lastlight-dispatch-1.0.0"
    for cell in result["trace"]:
        direct = simulate(
            scenario_at(request.scenario, cell["initial_soc"], cell["duration_hours"])
        )
        assert cell["failed"] == (not direct.summary.survived_full_window)
        assert cell["physics_verified"] is True


def test_exact_failure_at_exclusive_horizon_is_not_observed():
    baseline = SimulationRequest(duration_hours=9.12, step_minutes=15)
    exact = simulate(baseline)
    assert exact.summary.first_failure_utc is None
    assert observed_before_horizon(9.12, 9.12) is False
    assert observed_before_horizon(9.12, 9.121) is True
    edge = physics_frontier(
        FrontierRequest(
            scenario=baseline, soc_points=5, duration_points=3, maximum_hours=9.12
        )
    )
    baseline_soc = [
        cell for cell in edge["trace"] if abs(cell["initial_soc"] - 0.8) < 1e-12
    ]
    assert baseline_soc[-1]["failed"] is False


def test_api_keeps_incompatible_ml_checkpoint_out_of_physics_map():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/frontiers",
            json={"soc_points": 3, "duration_points": 3, "include_ml": True},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1.0.0"
    assert body["ml_model_version"] is None
    assert body["ml_status"] == "incompatible_checkpoint"
    assert body["ml_estimates"] == []
    assert all(cell["physics_verified"] for cell in body["trace"])


def test_frontier_refuses_to_extrapolate_supplied_profiles():
    scenario = SimulationRequest(solar={"profile_kw": [0.0] * 48}, duration_hours=12)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/frontiers",
            json={
                "scenario": scenario.model_dump(mode="json"),
                "maximum_hours": 13,
            },
        )
    assert response.status_code == 422


def test_offline_web_map_is_exact_official_result():
    root = Path(__file__).resolve().parents[2]
    fixture = json.loads(
        (root / "apps/web/src/data/frontier.result.json").read_text(encoding="utf-8")
    )
    assert fixture == physics_frontier(FrontierRequest())
