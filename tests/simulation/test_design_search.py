"""Deterministic design-search regression: always the official physics engine."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from services.simulation.api import app
from services.simulation.design_search import DesignSearchRequest, design_search
from services.simulation.engine import simulate
from services.simulation.frontier import FrontierRequest, physics_frontier
from services.simulation.schemas import SimulationRequest


def request(**kwargs):
    return {
        "scenario": {"duration_hours": 12, "grid": {"online": False}},
        "outage_target_hours": 12,
        "candidate_capacities_kwh": [36, 24, 32, 30],
        **kwargs,
    }


def test_reference_24_30_32_36_and_authentic_engine_identity():
    result = design_search(DesignSearchRequest.model_validate(request()))
    assert result.selected_capacity_kwh == 32
    assert [c.capacity_kwh for c in result.candidates] == [24, 30, 32, 36]
    assert [c.survived_target for c in result.candidates] == [
        False, False, True, True
    ]
    assert [c.first_critical_failure_hours for c in result.candidates] == [
        9.12, 11.4, None, None
    ]
    for c in result.candidates:
        candidate = SimulationRequest(battery={"capacity_kwh": c.capacity_kwh})
        physics = simulate(candidate)
        assert c.physics_run_id == physics.run_id
        assert c.physics_input_hash == physics.input_hash
        assert c.unserved_critical_kwh == physics.summary.unserved_critical_kwh
        assert c.ending_soc == physics.summary.ending_soc
        assert c.first_critical_failure_utc == physics.summary.first_failure_utc
        assert c.valid and c.infeasibility_reasons == (
            [] if c.survived_target else ["critical_energy_unserved_during_target"]
        )
    assert result.physics_verified is True
    assert result.provenance.category == "synthetic"


def test_fully_precharged_24_survives_without_changing_constraints():
    data = request(
        candidate_capacities_kwh=[24],
        scenario={"battery": {"initial_soc": 1}, "duration_hours": 12},
    )
    result = design_search(DesignSearchRequest.model_validate(data))
    assert result.selected_capacity_kwh == 24
    assert result.candidates[0].first_critical_failure_hours is None
    assert result.candidates[0].unserved_critical_kwh == 0


@pytest.mark.parametrize("step", [1, 5, 15, 60])
def test_step_lengths_preserve_event_split_and_pass_boundary(step):
    exact = request(
        scenario={"duration_hours": 9.12, "step_minutes": step},
        outage_target_hours=9.12,
        candidate_capacities_kwh=[24],
    )
    at_end = design_search(DesignSearchRequest.model_validate(exact))
    assert at_end.candidates[0].survived_target is True
    assert at_end.candidates[0].first_critical_failure_hours is None
    assert at_end.selected_capacity_kwh == 24
    longer = request(
        scenario={"duration_hours": 9.121, "step_minutes": step},
        outage_target_hours=9.121,
        candidate_capacities_kwh=[24],
    )
    beyond = design_search(DesignSearchRequest.model_validate(longer))
    assert beyond.candidates[0].survived_target is False
    assert beyond.candidates[0].first_critical_failure_hours == 9.12


def test_no_feasible_candidate_and_inverter_physics_limit():
    req = DesignSearchRequest.model_validate(
        request(
            candidate_capacities_kwh=[24, 36],
            scenario={"inverter": {"max_kw": 1}, "duration_hours": 12},
        )
    )
    result = design_search(req)
    assert result.selected_capacity_kwh is None
    assert all(not c.survived_target for c in result.candidates)
    assert all(
        "inverter_limit_below_critical_load" in c.infeasibility_reasons
        for c in result.candidates
    )


def test_islanding_disabled_cannot_pass():
    data = request(
        candidate_capacities_kwh=[36, 60],
        scenario={"inverter": {"islanding_capable": False}},
    )
    result = design_search(DesignSearchRequest.model_validate(data))
    assert result.selected_capacity_kwh is None
    assert all(
        "inverter_islanding_disabled" in c.infeasibility_reasons
        for c in result.candidates
    )


def test_solar_islanded_changes_physics_result():
    without = design_search(
        DesignSearchRequest.model_validate(
            request(candidate_capacities_kwh=[24])
        )
    )
    with_solar = design_search(
        DesignSearchRequest.model_validate(
            request(
                candidate_capacities_kwh=[24],
                scenario={
                    "solar": {"generation_kw": 0.5, "islanding_capable": True}
                },
            )
        )
    )
    assert without.selected_capacity_kwh is None
    assert with_solar.selected_capacity_kwh == 24
    assert with_solar.candidates[0].unserved_critical_kwh == 0


def test_supplied_profile_does_not_get_reordered_or_recomputed():
    profile = [0.0] * 24 + [1.0] * 24
    req = request(
        scenario={
            "duration_hours": 12,
            "step_minutes": 15,
            "solar": {"profile_kw": profile, "islanding_capable": True},
            "grid": {"profile_online": [False] * 48},
        },
        candidate_capacities_kwh=[18, 24],
    )
    result = design_search(DesignSearchRequest.model_validate(req))
    for row in result.candidates:
        direct = simulate(
            SimulationRequest.model_validate({
                **req["scenario"],
                "battery": {"capacity_kwh": row.capacity_kwh},
            })
        )
        assert row.physics_run_id == direct.run_id
        assert row.unserved_critical_kwh == direct.summary.unserved_critical_kwh


def test_order_independence_and_deterministic_result_identity():
    a = design_search(DesignSearchRequest.model_validate(request()))
    b = design_search(
        DesignSearchRequest.model_validate(
            request(candidate_capacities_kwh=[30, 32, 24, 36])
        )
    )
    assert a.model_dump() == b.model_dump()
    assert a.run_id == design_search(
        DesignSearchRequest.model_validate(request())
    ).run_id


def test_optional_costs_are_user_annotations_not_optimization():
    costs = [
        {"capacity_kwh": x, "amount": amount, "currency": "USD",
         "basis": "same user-provided scope"}
        for x, amount in [(30, 5), (32, 1000), (24, 1), (36, 4)]
    ]
    chosen = design_search(
        DesignSearchRequest.model_validate(request(comparable_costs=costs))
    )
    assert chosen.selected_capacity_kwh == 32
    assert chosen.candidates[2].comparable_cost.amount == 1000
    same = design_search(
        DesignSearchRequest.model_validate(request(
            candidate_capacities_kwh=[32, 24, 36, 30],
            comparable_costs=list(reversed(costs)),
        ))
    )
    assert same.model_dump() == chosen.model_dump()


@pytest.mark.parametrize("change", [
    {"candidate_capacities_kwh": []},
    {"candidate_capacities_kwh": [24, 24]},
    {"candidate_capacities_kwh": [-1]},
    {"candidate_capacities_kwh": [0]},
    {"candidate_capacities_kwh": [20001]},
    {"candidate_capacities_kwh": ["24"]},
    {"candidate_capacities_kwh": [float("inf")]},
    {"candidate_capacities_kwh": [float("nan")]},
    {"candidate_capacities_kwh": list(range(1, 34))},
    {"outage_target_hours": 11},
    {"outage_target_hours": 0},
    {"scenario": {"grid": {"online": True}}},
    {"scenario": {"grid": {"profile_online": [True] * 48}}},
    {"scenario": {"duration_hours": 168, "step_minutes": 1},
     "outage_target_hours": 168,
     "candidate_capacities_kwh": list(range(1, 5))},
    {"comparable_costs": []},
    {"comparable_costs": [
        {"capacity_kwh": 24, "amount": -1, "currency": "USD", "basis": "all"}
    ]},
])
def test_invalid_candidate_or_outage_strictly_rejected(change):
    with pytest.raises(ValidationError):
        DesignSearchRequest.model_validate(request(**change))


def test_api_validation_including_nonfinite_json():
    with TestClient(app) as client:
        for bad in [{"candidate_capacities_kwh": [30, 30]}, {
            "scenario": {"grid": {"online": True}}
        }]:
            response = client.post("/api/v1/design-search", json=request(**bad))
            assert response.status_code == 422
            assert response.json()["error"]["code"] == "validation_error"
        raw = '{"scenario":{},"outage_target_hours":12,"candidate_capacities_kwh":[NaN]}'
        response = client.post(
            "/api/v1/design-search", content=raw,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422
        assert "NaN" not in response.text


def test_http_response_is_reproducible_and_backward_compatible():
    with TestClient(app) as client:
        response = client.post("/api/v1/design-search", json=request())
        assert response.status_code == 200, response.text
        assert response.json()["selected_capacity_kwh"] == 32
        assert client.post("/api/v1/design-search", json=request()).json() == (
            response.json()
        )
        assert client.post("/api/v1/simulations", json={}).status_code == 200
        assert client.post("/api/v1/comparisons", json={}).status_code == 200
        assert client.post("/api/v1/frontiers", json={
            "soc_points": 3, "duration_points": 3
        }).status_code == 200
        spec = client.get("/openapi.json").json()
        assert "/api/v1/design-search" in spec["paths"]


def test_unmodified_frontier_still_matches_prior_contract():
    frontier = physics_frontier(FrontierRequest(soc_points=3, duration_points=3))
    assert frontier["summary"]["physics_calls"] == 3
    assert frontier["summary"]["verified_cells"] == 9
    assert all(item["physics_verified"] for item in frontier["trace"])
