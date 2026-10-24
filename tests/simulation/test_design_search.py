"""Capacity selection is verified by independent calls to the official engine."""

import hashlib
import itertools
import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from services.simulation import design_search
from services.simulation.api import app
from services.simulation.design_search import (
    DesignSearchRequest,
    DesignSearchResult,
    search_designs,
)
from services.simulation.engine import EnergyBalanceError, simulate
from services.simulation.frontier import FrontierRequest, physics_frontier
from services.simulation.schemas import ErrorResponse, SimulationRequest

REFERENCE = {
    "scenario": {},
    "outage_hours": 12,
    "candidate_capacities_kwh": [24, 30, 32, 36],
}


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def checked_search(client, body):
    response = client.post("/api/v1/design-search", json=body)
    assert response.status_code == 200, response.text
    result = response.json()
    DesignSearchResult.model_validate(result)
    assert (
        digest({k: v for k, v in result.items() if k != "result_hash"})
        == result["result_hash"]
    )
    assert digest(result["input"]) == result["input_hash"]
    for candidate in result["candidates"]:
        direct = client.post("/api/v1/simulations", json=candidate["input"]).json()
        assert candidate["valid"] is True
        assert candidate["summary"] == direct["summary"]
        assert candidate["simulation_run_id"] == direct["run_id"]
        assert candidate["simulation_input_hash"] == direct["input_hash"]
        assert candidate["simulation_result_hash"] == digest(direct)
        assert candidate["provenance"] == direct["provenance"]
        assert (
            candidate["model_version"]
            == direct["model_version"]
            == "lastlight-dispatch-1.0.0"
        )
        assert candidate["schema_version"] == direct["schema_version"] == "1.0.0"
        assert candidate["feasible"] == direct["summary"]["survived_full_window"]
    return result


@pytest.mark.parametrize("step", [1, 7, 15, 60])
def test_reference_ranking_uses_observed_results_and_exact_split_intervals(
    client, step
):
    result = checked_search(client, {**REFERENCE, "scenario": {"step_minutes": step}})
    assert result["status"] == "feasible_candidate_found"
    assert result["selected_capacity_kwh"] == 32
    assert result["physics_calls"] == 4
    assert [c["capacity_kwh"] for c in result["candidates"]] == [24, 30, 32, 36]
    for candidate, event, unserved in zip(
        result["candidates"], [9.12, 11.4, None, None], [4.32, 0.9, 0, 0]
    ):
        summary = candidate["summary"]
        assert summary["critical_survival_hours"] == event
        assert summary["unserved_critical_kwh"] == pytest.approx(unserved)
        assert candidate["feasible"] == (event is None)
        assert candidate["infeasibility_reasons"] == (
            [] if event is None else ["critical_shortfall_within_outage"]
        )
        direct = simulate(SimulationRequest.model_validate(candidate["input"]))
        if event is not None:
            point = next(p for p in direct.trace if p.unserved_critical_kw > 1e-9)
            assert point.elapsed_hours == pytest.approx(event)
            assert point.t_utc == summary["first_failure_utc"]
        assert sum(p.duration_hours for p in direct.trace) == pytest.approx(12)
        assert direct.trace[-1].battery_soc_end == summary["ending_soc"]
    assert (
        result["selected_simulation_run_id"]
        == result["candidates"][2]["simulation_run_id"]
    )


def test_precharged_24_kwh_and_unchanged_16h_regressions(client):
    result = checked_search(
        client,
        {
            **REFERENCE,
            "scenario": {"battery": {"initial_soc": 1}},
            "candidate_capacities_kwh": [24],
        },
    )
    candidate = result["candidates"][0]
    assert result["selected_capacity_kwh"] == 24
    assert candidate["summary"]["critical_survival_hours"] is None
    assert candidate["summary"]["idealized_autonomy_hours"] == 12.16
    for capacity, soc, expected in [(24, 0.8, 9.12), (36, 0.8, 13.68), (24, 1, 12.16)]:
        long = checked_search(
            client,
            {
                "scenario": {"duration_hours": 16, "battery": {"initial_soc": soc}},
                "outage_hours": 16,
                "candidate_capacities_kwh": [capacity],
            },
        )
        assert long["candidates"][0]["summary"]["critical_survival_hours"] == expected
        assert long["selected_capacity_kwh"] is None


@pytest.mark.parametrize("step", [1, 7, 15, 60])
def test_exclusive_horizon_is_censored_and_positive_shortfall_is_not(client, step):
    body = {
        "scenario": {"step_minutes": step},
        "outage_hours": 9.12,
        "candidate_capacities_kwh": [24],
    }
    exact = checked_search(client, body)
    assert exact["selected_capacity_kwh"] == 24
    assert exact["candidates"][0]["summary"]["first_failure_utc"] is None
    later = checked_search(client, {**body, "outage_hours": 9.1201})
    assert later["status"] == "no_feasible_candidate"
    assert later["candidates"][0]["summary"]["critical_survival_hours"] == 9.12


@pytest.mark.parametrize(
    "constraint",
    [
        {"inverter": {"max_kw": 1}},
        {"inverter": {"islanding_capable": False}},
        {"battery": {"max_discharge_kw": 1}},
    ],
)
def test_more_capacity_cannot_fix_inverter_or_discharge_power_infeasibility(
    client, constraint
):
    result = checked_search(
        client,
        {
            **REFERENCE,
            "scenario": constraint,
            "candidate_capacities_kwh": [24, 36, 20_000],
        },
    )
    assert result["status"] == "no_feasible_candidate"
    assert (
        result["selected_capacity_kwh"] is result["selected_simulation_run_id"] is None
    )
    assert all(
        c["summary"]["critical_survival_hours"] == 0 for c in result["candidates"]
    )
    assert all(c["infeasibility_reasons"] for c in result["candidates"])


def test_no_feasible_candidate_is_a_successful_completed_search(client):
    result = checked_search(client, {**REFERENCE, "candidate_capacities_kwh": [30, 24]})
    assert result["status"] == "no_feasible_candidate"
    assert result["selected_capacity_kwh"] is None
    assert len(result["candidates"]) == result["physics_calls"] == 2


def test_solar_and_islanding_come_from_official_dispatch(client):
    body = {
        **REFERENCE,
        "scenario": {"solar": {"generation_kw": 1, "islanding_capable": True}},
        "candidate_capacities_kwh": [4, 12, 24],
    }
    result = checked_search(client, body)
    assert result["selected_capacity_kwh"] == 12
    assert result["candidates"][0]["summary"][
        "critical_survival_hours"
    ] == pytest.approx(4.56)
    dark = checked_search(
        client,
        {
            **body,
            "scenario": {"solar": {"generation_kw": 1, "islanding_capable": False}},
        },
    )
    assert dark["selected_capacity_kwh"] is None
    assert all(c["summary"]["solar_used_kwh"] == 0 for c in dark["candidates"])


def test_target_prefix_slices_profiles_without_changing_load_soc_or_inverter(client):
    scenario = SimulationRequest.model_validate(
        {
            "duration_hours": 6,
            "step_minutes": 60,
            "battery": {
                "initial_soc": 0.7,
                "minimum_soc": 0.3,
                "max_charge_kw": 2,
                "max_discharge_kw": 4,
            },
            "load": {
                "critical_kw": 2,
                "noncritical_kw": 1,
                "shed_noncritical_during_outage": False,
            },
            "inverter": {"max_kw": 4},
            "solar": {"islanding_capable": True, "profile_kw": [0, 3, 0, 3, 1, 500]},
            "grid": {"online": True, "profile_online": [False] * 5 + [True]},
        }
    ).model_dump(mode="json")
    original = json.loads(json.dumps(scenario))
    result = checked_search(
        client,
        {
            "scenario": scenario,
            "outage_hours": 4.5,
            "candidate_capacities_kwh": [24, 32],
        },
    )
    assert scenario == original
    for c in result["candidates"]:
        expected = json.loads(json.dumps(original))
        expected["battery"]["capacity_kwh"] = c["capacity_kwh"]
        expected["duration_hours"] = 4.5
        expected["solar"]["profile_kw"] = expected["solar"]["profile_kw"][:5]
        expected["grid"]["profile_online"] = [False] * 5
        assert c["input"] == expected
        trace = simulate(SimulationRequest.model_validate(c["input"])).trace
        assert trace[-1].t_end_utc == "2026-01-01T04:30:00Z"
    assert (
        client.post(
            "/api/v1/design-search",
            json={
                "scenario": scenario,
                "outage_hours": 6,
                "candidate_capacities_kwh": [24],
            },
        ).status_code
        == 422
    )


def test_degraded_noncritical_service_does_not_disqualify_critical_survival(client):
    result = checked_search(client, {**REFERENCE, "candidate_capacities_kwh": [32]})
    candidate = result["candidates"][0]
    assert candidate["feasible"] is True
    assert candidate["summary"]["unserved_noncritical_kwh"] == 24
    assert candidate["summary"]["unserved_critical_kwh"] == 0


def test_all_candidate_orders_have_identical_results_and_no_early_exit(monkeypatch):
    calls = []

    def official(request):
        calls.append(request.battery.capacity_kwh)
        return simulate(request)

    monkeypatch.setattr(design_search, "simulate", official)
    expected = search_designs(DesignSearchRequest.model_validate(REFERENCE))
    for order in itertools.permutations([24, 30, 32, 36]):
        calls.clear()
        request = DesignSearchRequest.model_validate(
            {**REFERENCE, "candidate_capacities_kwh": list(order)}
        )
        before = request.model_dump_json()
        assert search_designs(request) == expected
        assert calls == [24, 30, 32, 36]
        assert request.model_dump_json() == before


def test_costs_are_comparable_annotations_and_never_override_capacity_ranking(client):
    costs = {
        "currency": "USD",
        "basis": "Synthetic test totals; not market quotations",
        "entries": [
            {"capacity_kwh": c, "amount": amount}
            for c, amount in [(36, 0), (32, 20), (30, 30), (24, 40)]
        ],
    }
    body = {**REFERENCE, "costs": costs}
    result = checked_search(client, body)
    assert result["selected_capacity_kwh"] == 32
    assert [c["cost_amount"] for c in result["candidates"]] == [40, 30, 20, 0]
    reordered = {
        **body,
        "candidate_capacities_kwh": [36, 32, 30, 24],
        "costs": {**costs, "entries": costs["entries"][::-1]},
    }
    assert checked_search(client, reordered) == result
    unpriced = checked_search(client, REFERENCE)
    assert unpriced["input_hash"] != result["input_hash"]
    assert [c["simulation_result_hash"] for c in unpriced["candidates"]] == [
        c["simulation_result_hash"] for c in result["candidates"]
    ]


def test_default_resolution_utc_normalization_and_parallel_replay(client):
    expected = checked_search(client, REFERENCE)
    body = {
        **REFERENCE,
        "scenario": SimulationRequest(start_utc="2026-01-01T06:00:00+06:00").model_dump(
            mode="json"
        ),
    }
    assert checked_search(client, body) == expected
    request = DesignSearchRequest.model_validate(body)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: search_designs(request), range(8)))
    assert all(result.model_dump(mode="json") == expected for result in results)
    changed = checked_search(client, {**REFERENCE, "scenario": {"seed": 1}})
    assert changed["input_hash"] != expected["input_hash"]
    assert changed["selected_capacity_kwh"] == expected["selected_capacity_kwh"]


def test_search_and_existing_frontier_agree_at_same_scenario_and_horizon(client):
    result = checked_search(client, REFERENCE)
    for c in result["candidates"]:
        frontier = physics_frontier(
            FrontierRequest(
                scenario=SimulationRequest.model_validate(c["input"]),
                soc_points=5,
                duration_points=3,
            )
        )
        cell = next(
            cell
            for cell in frontier["trace"]
            if abs(cell["initial_soc"] - 0.8) < 1e-12 and cell["duration_hours"] == 12
        )
        assert cell["failed"] == (not c["feasible"])


INVALID = [
    {"candidate_capacities_kwh": []},
    {"candidate_capacities_kwh": [24, 24.0]},
    {"candidate_capacities_kwh": [0]},
    {"candidate_capacities_kwh": [-1]},
    {"candidate_capacities_kwh": [0.0001]},
    {"candidate_capacities_kwh": [20_001]},
    {"candidate_capacities_kwh": [True]},
    {"candidate_capacities_kwh": ["24"]},
    {"candidate_capacities_kwh": [None]},
    {"candidate_capacities_kwh": list(range(1, 34))},
    {"outage_hours": 0},
    {"outage_hours": 169},
    {"outage_hours": 13},
    {"outage_hours": "12"},
    {"outage_hours": True},
    {"scenario": {"grid": {"online": True}}},
    {"scenario": {"grid": {"profile_online": [False] * 47 + [True]}}},
    {"scenario": {"solar": {"profile_kw": [0]}}},
    {"scenario": {"battery": {"capacity_kwh": -1}}},
    {"scenario": {"battery": {"initial_soc": 0.1}}},
    {"scenario": {"load": {"critical_profile_kw": [1.5] * 48}}},
    {
        "scenario": {"duration_hours": 24, "step_minutes": 1},
        "outage_hours": 24,
        "candidate_capacities_kwh": list(range(1, 15)),
    },
    {"unknown": 1},
]


@pytest.mark.parametrize("changes", INVALID)
def test_invalid_search_is_atomic_structured_422_before_any_simulation(
    client, changes, monkeypatch
):
    def forbidden(_):
        pytest.fail("Invalid search must not call the simulator")

    monkeypatch.setattr(design_search, "simulate", forbidden)
    response = client.post(
        "/api/v1/design-search",
        json={**REFERENCE, **changes},
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 422
    error = ErrorResponse.model_validate(response.json())
    assert error.error.code == "validation_error" and error.error.details
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


@pytest.mark.parametrize(
    "costs",
    [
        {
            "currency": "usd",
            "basis": "test",
            "entries": [{"capacity_kwh": 24, "amount": 1}],
        },
        {
            "currency": "USD",
            "basis": " ",
            "entries": [{"capacity_kwh": 24, "amount": 1}],
        },
        {"currency": "USD", "basis": "test", "entries": []},
        {
            "currency": "USD",
            "basis": "test",
            "entries": [{"capacity_kwh": 24, "amount": -1}],
        },
        {
            "currency": "USD",
            "basis": "test",
            "entries": [{"capacity_kwh": 24, "amount": 1e13}],
        },
        {
            "currency": "USD",
            "basis": "test",
            "entries": [{"capacity_kwh": 24, "amount": "1"}],
        },
        {
            "currency": "USD",
            "basis": "test",
            "entries": [{"capacity_kwh": 24, "amount": 1}] * 2,
        },
        {
            "currency": "USD",
            "basis": "test",
            "entries": [{"capacity_kwh": c, "amount": 1} for c in [24, 30, 32]],
        },
        {
            "currency": "USD",
            "basis": "test",
            "entries": [{"capacity_kwh": c, "amount": 1} for c in [24, 30, 32, 48]],
        },
        {
            "currency": "USD",
            "basis": "test",
            "entries": [
                {"capacity_kwh": c, "amount": 1, "currency": "EUR"}
                for c in [24, 30, 32, 36]
            ],
        },
    ],
)
def test_incomparable_or_invalid_costs_are_rejected(client, costs):
    assert (
        client.post(
            "/api/v1/design-search", json={**REFERENCE, "costs": costs}
        ).status_code
        == 422
    )


@pytest.mark.parametrize(
    "raw",
    [
        '{"scenario":{},"outage_hours":12,"candidate_capacities_kwh":[NaN]}',
        '{"scenario":{},"outage_hours":Infinity,"candidate_capacities_kwh":[24]}',
        "{bad json",
        "null",
        "[]",
        "{}",
    ],
)
def test_nonfinite_malformed_and_missing_search_input_is_422(client, raw):
    response = client.post(
        "/api/v1/design-search",
        content=raw,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert "NaN" not in response.text and "Infinity" not in response.text


def test_budget_boundary_and_official_capacity_endpoints_are_validated():
    body = {
        "scenario": {"duration_hours": 50, "step_minutes": 3},
        "outage_hours": 50,
        "candidate_capacities_kwh": list(range(1, 21)),
    }
    request = DesignSearchRequest.model_validate(body)
    assert (
        request.scenario.interval_count * len(request.candidate_capacities_kwh)
        == 20_000
    )
    with pytest.raises(ValidationError):
        DesignSearchRequest.model_validate(
            {
                **body,
                "scenario": {"duration_hours": 51, "step_minutes": 3},
                "outage_hours": 50.05,
            }
        )
    DesignSearchRequest.model_validate(
        {**REFERENCE, "candidate_capacities_kwh": [0.001, 20_000]}
    )


def test_python_validation_bypass_is_rejected():
    request = DesignSearchRequest.model_validate(REFERENCE)
    with pytest.raises(ValidationError):
        search_designs(request.model_copy(update={"candidate_capacities_kwh": [-1]}))
    with pytest.raises(ValidationError):
        search_designs(request.model_copy(update={"outage_hours": 13}))


def test_zero_critical_load_is_explicitly_warned(client):
    result = checked_search(
        client,
        {
            **REFERENCE,
            "scenario": {"load": {"critical_kw": 0}},
            "candidate_capacities_kwh": [0.001],
        },
    )
    assert result["selected_capacity_kwh"] == 0.001
    assert any("No critical demand" in warning for warning in result["warnings"])


def test_simulator_invariant_failure_aborts_search_instead_of_skipping_candidate(
    client, monkeypatch
):
    def broken(_):
        raise EnergyBalanceError("private test invariant")

    monkeypatch.setattr(design_search, "simulate", broken)
    response = client.post("/api/v1/design-search", json=REFERENCE)
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "energy_balance_error"
    assert "private test invariant" not in response.text


def test_design_search_openapi_has_typed_response_and_existing_cors(client):
    spec = client.get("/openapi.json").json()
    route = spec["paths"]["/api/v1/design-search"]["post"]
    assert route["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/DesignSearchResult")
    assert "422" in route["responses"] and "500" in route["responses"]
    response = client.options(
        "/api/v1/design-search",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
