"""Physics-only Failure Frontier adapted from Askar's PR #7 research map.

The dispatch engine and v1 schemas remain owned by the official Physics API.
The 1.1.0 ML checkpoint is not compatible with this 1.0.0 runtime.
"""

import hashlib
import json
from math import ceil
from uuid import NAMESPACE_URL, uuid5

from pydantic import Field, model_validator

from . import MODEL_VERSION, SCHEMA_VERSION
from .engine import simulate
from .schemas import Contract, SimulationRequest


class FrontierRequest(Contract):
    scenario: SimulationRequest = Field(default_factory=SimulationRequest)
    soc_points: int = Field(default=13, ge=3, le=41)
    duration_points: int = Field(default=21, ge=3, le=49)
    maximum_hours: float = Field(default=12, ge=0.25, le=48)
    include_ml: bool = False

    @model_validator(mode="after")
    def budget_and_profiles(self):
        if self.soc_points * self.duration_points > 1600:
            raise ValueError("Frontier exceeds the 1600-cell computation budget")
        if self.maximum_hours < 0.25:
            raise ValueError("maximum_hours must be at least 0.25")
        if self.maximum_hours > self.scenario.duration_hours and (
            self.scenario.solar.profile_kw is not None
            or self.scenario.grid.profile_online is not None
        ):
            raise ValueError("Frontier cannot extrapolate supplied time profiles")
        return self


def scenario_at(
    scenario: SimulationRequest, initial_soc: float, duration_hours: float
) -> SimulationRequest:
    body = scenario.model_dump(mode="json")
    body["battery"]["initial_soc"] = initial_soc
    body["duration_hours"] = duration_hours
    count = ceil(duration_hours * 60 / scenario.step_minutes)
    for owner, field in (("solar", "profile_kw"), ("grid", "profile_online")):
        if body[owner][field] is not None:
            if count > len(body[owner][field]):
                raise ValueError("Frontier cannot extrapolate supplied time profiles")
            body[owner][field] = body[owner][field][:count]
    return SimulationRequest.model_validate(body)


def observed_before_horizon(failure_hours: float | None, horizon_hours: float) -> bool:
    # The run's observation interval is [0, horizon), so equality is censored.
    return failure_hours is not None and horizon_hours > failure_hours + 1e-10


def physics_frontier(request: FrontierRequest) -> dict:
    scenario = request.scenario
    low, high = scenario.battery.minimum_soc, scenario.battery.maximum_soc
    socs = [
        low
        if index == 0
        else high
        if index == request.soc_points - 1
        else low + (high - low) * index / (request.soc_points - 1)
        for index in range(request.soc_points)
    ]
    horizons = [
        0.25 + (request.maximum_hours - 0.25) * index / (request.duration_points - 1)
        for index in range(request.duration_points)
    ]
    cells = []
    for soc in socs:
        trace = simulate(scenario_at(scenario, soc, request.maximum_hours))
        failure = trace.summary.critical_survival_hours
        for horizon in horizons:
            failed = observed_before_horizon(failure, horizon)
            cells.append(
                {
                    "initial_soc": soc,
                    "duration_hours": horizon,
                    "failed": failed,
                    "first_failure_hours": failure if failed else None,
                    "physics_verified": True,
                    "verification_run_id": trace.run_id,
                }
            )
    identity = {
        "scenario": scenario.model_dump(mode="json"),
        "soc_points": request.soc_points,
        "duration_points": request.duration_points,
        "maximum_hours": request.maximum_hours,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    warnings = [
        "One official v1 physics trace per SOC column; shorter horizons classify trace prefixes."
    ]
    if request.include_ml:
        warnings.append(
            "ML proposals unavailable: PR #7 checkpoint targets physics/schema 1.1.0; official runtime is 1.0.0."
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "physics_version": MODEL_VERSION,
        "ml_model_version": None,
        "ml_status": "incompatible_checkpoint"
        if request.include_ml
        else "not_requested",
        "run_id": str(uuid5(NAMESPACE_URL, f"frontier:{MODEL_VERSION}:{digest}")),
        "input_hash": digest,
        "seed": scenario.seed,
        "provenance": scenario.provenance.model_dump(mode="json"),
        "summary": {
            "physics_calls": request.soc_points,
            "verified_cells": len(cells),
            "method": "one official physics trace per SOC column; exclusive horizon classification",
        },
        "axes": {"initial_soc": socs, "duration_hours": horizons},
        "trace": cells,
        "ml_estimates": [],
        "warnings": warnings,
    }
