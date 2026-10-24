import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from services.simulation import api
from services.simulation.engine import EnergyBalanceError, compare, simulate
from services.simulation.fixtures import artifacts
from services.simulation.schemas import (
    ComparisonRequest,
    ErrorResponse,
    SimulationRequest,
    SimulationResult,
)


@pytest.fixture
def client():
    with TestClient(api.app, raise_server_exceptions=False) as client:
        yield client


@pytest.mark.parametrize(
    "body",
    [
        {"battery": {"capacity_kwh": 0}},
        {"battery": {"capacity_kwh": -1}},
        {"battery": {"initial_soc": 80}},
        {"battery": {"initial_soc": 0.1}},
        {"battery": {"minimum_soc": 0.8, "maximum_soc": 0.8}},
        {"battery": {"maximum_soc": 0.7}},
        {"battery": {"charge_efficiency": 0}},
        {"battery": {"discharge_efficiency": 1.1}},
        {"battery": {"discharge_efficiency": 1e-300}},
        {"battery": {"max_charge_kw": -1}},
        {"inverter": {"max_kw": -1}},
        {"solar": {"generation_kw": -1}},
        {"load": {"critical_kw": -1}},
        {"grid": {"import_limit_kw": -1}},
        {"duration_hours": 0},
        {"duration_hours": 169},
        {"step_minutes": 0},
        {"step_minutes": 61},
        {"step_minutes": 15.5},
        {"start_utc": "2026-01-01T00:00:00"},
        {"start_utc": "not-a-time"},
        {"start_utc": "9999-12-31T23:59:59Z"},
        {"start_utc": 1000},
        {"seed": -1},
        {"seed": 2**32},
        {"seed": True},
        {"battery": {"capacity_kwh": "24"}},
        {"battery": {"capacity_kwh": True}},
        {"grid": {"online": 1}},
        {"inverter": {"islanding_capable": "true"}},
        {"solar": {"profile_kw": []}},
        {"solar": {"profile_kw": [1]}},
        {"grid": {"profile_online": [False]}},
        {"grid": {"profile_online": [0] * 48}},
        {"unknown": 1},
        {"battery": {"unknown": 1}},
        {"battery": None},
        {"provenance": {"category": "guess"}},
        {"provenance": {"references": [""]}},
    ],
)
def test_invalid_input_is_structured_422(client, body):
    response = client.post("/api/v1/simulations", json=body)
    assert response.status_code == 422
    error = ErrorResponse.model_validate(response.json())
    assert error.error.code == "validation_error"
    assert error.error.details
    assert all(d.location[0] == "body" for d in error.error.details)


@pytest.mark.parametrize(
    "raw",
    [
        '{"battery":{"capacity_kwh":NaN}}',
        '{"solar":{"generation_kw":Infinity}}',
        '{"battery":{"initial_soc":-Infinity}}',
        "{bad json",
        "null",
        "[]",
    ],
)
def test_nonfinite_and_malformed_json_do_not_break_error_serializer(client, raw):
    response = client.post(
        "/api/v1/simulations", content=raw, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert "NaN" not in response.text and "Infinity" not in response.text


def test_health_and_openapi(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    spec = client.get("/openapi.json").json()
    assert {"/health", "/api/v1/simulations", "/api/v1/comparisons"} <= spec[
        "paths"
    ].keys()
    assert "ErrorResponse" in spec["components"]["schemas"]
    assert client.get("/docs").status_code == 200


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
)
def test_cors_local_origins(client, origin):
    response = client.options(
        "/api/v1/simulations",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_cors_rejects_external_origin_and_error_retains_cors(client):
    response = client.options(
        "/api/v1/simulations",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
    bad = client.post(
        "/api/v1/simulations",
        json={"seed": -1},
        headers={"Origin": "http://localhost:5173"},
    )
    assert bad.status_code == 422
    assert bad.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_utc_normalization_and_default_resolution_preserve_hash(client):
    utc = client.post("/api/v1/simulations", json={}).json()
    offset = client.post(
        "/api/v1/simulations", json={"start_utc": "2026-01-01T06:00:00+06:00"}
    ).json()
    assert utc == offset
    assert client.post("/api/v1/simulations", json=utc["input"]).json() == utc
    changed = client.post("/api/v1/simulations", json={"seed": 1}).json()
    assert (
        changed["run_id"] != utc["run_id"]
        and changed["input_hash"] != utc["input_hash"]
    )
    assert changed["trace"] == utc["trace"]
    assert (
        SimulationResult.model_validate(utc).input.start_utc.utcoffset().total_seconds()
        == 0
    )


def test_parallel_calls_are_stateless():
    request = SimulationRequest()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(
            pool.map(lambda _: simulate(request).model_dump_json(), range(8))
        )
    assert len(set(results)) == 1


@pytest.mark.parametrize(
    "upgrade,expected", [("battery_36_kwh", 13.68), ("full_precharge", 12.16)]
)
def test_parameterized_comparison_endpoint(client, upgrade, expected):
    response = client.post(
        "/api/v1/comparisons",
        json={"baseline": {"duration_hours": 16}, "upgrade": upgrade},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["baseline"]["summary"]["critical_survival_hours"] == 9.12
    assert body["upgraded"]["summary"]["critical_survival_hours"] == expected
    assert body["delta"]["critical_survival_hours"] == pytest.approx(expected - 9.12)
    assert body["delta"]["unserved_critical_kwh"] < 0
    for side in ["baseline", "upgraded"]:
        request = body[side]["input"]
        assert client.post("/api/v1/simulations", json=request).json() == body[side]


def test_comparison_censoring_is_not_infinite_autonomy(client):
    body = client.post("/api/v1/comparisons", json={}).json()
    assert body["upgraded"]["summary"]["critical_survival_hours"] is None
    assert body["delta"]["critical_survival_hours"] is None
    assert body["upgraded"]["summary"]["idealized_autonomy_hours"] == 13.68


@pytest.mark.parametrize(
    "body",
    [
        {"upgrade": "unknown"},
        {"baseline": {"battery": {"capacity_kwh": 36}}},
        {"upgrade": "full_precharge", "baseline": {"battery": {"maximum_soc": 0.9}}},
    ],
)
def test_invalid_comparison(client, body):
    assert client.post("/api/v1/comparisons", json=body).status_code == 422


def test_python_callers_are_revalidated():
    with pytest.raises(ValidationError):
        simulate(SimulationRequest().model_copy(update={"duration_hours": -1}))
    with pytest.raises(ValidationError):
        compare(ComparisonRequest().model_copy(update={"upgrade": "unknown"}))


def test_internal_invariant_violation_is_not_exposed_as_a_valid_trace(
    client, monkeypatch
):
    def broken(_request):
        raise EnergyBalanceError("private implementation detail")

    monkeypatch.setattr(api, "simulate", broken)
    response = client.post("/api/v1/simulations", json={})
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "energy_balance_error"
    assert "private implementation detail" not in response.text


def test_unexpected_error_is_structured(client, monkeypatch):
    def broken(_request):
        raise RuntimeError("private implementation detail")

    monkeypatch.setattr(api, "simulate", broken)
    response = client.post("/api/v1/simulations", json={})
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "private implementation detail" not in response.text


def test_missing_endpoint_error_is_structured(client):
    assert client.get("/api/v1/does-not-exist").json()["error"]["code"] == "http_error"


def test_frozen_fixtures_and_schemas_match_real_api():
    root = Path(__file__).resolve().parents[2] / "docs" / "physics"
    for path, expected in artifacts().items():
        assert json.loads((root / path).read_text(encoding="utf-8")) == expected, path
