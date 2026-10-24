"""Bounded capacity enumeration through the unchanged official dispatch engine.

No autonomy formula, monotonicity assumption, equipment catalogue or cost
optimiser is used. Every candidate gets its own complete official simulation.
"""

from __future__ import annotations

import hashlib
import json
from math import ceil
from typing import Annotated, Literal, Self
from uuid import NAMESPACE_URL, uuid5

from pydantic import Field, field_validator, model_validator

from . import MODEL_VERSION, SCHEMA_VERSION
from .engine import simulate
from .schemas import Contract, Provenance, SimulationRequest, SimulationSummary

SEARCH_VERSION = "lastlight-battery-search-1.0.0"
MAX_CANDIDATES = 32
MAX_BASE_INTERVALS = 20_000
# Same capacity bounds as the official Battery contract; no new hardware limits.
Capacity = Annotated[float, Field(ge=0.001, le=20_000)]
Amount = Annotated[float, Field(ge=0, le=1e12)]


class CapacityCost(Contract):
    capacity_kwh: Capacity
    amount: Amount


class ComparableCosts(Contract):
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    basis: str = Field(min_length=1, max_length=200)
    entries: list[CapacityCost] = Field(min_length=1, max_length=MAX_CANDIDATES)

    @field_validator("basis")
    @classmethod
    def meaningful_basis(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Cost basis must describe comparable included items")
        return value


class DesignSearchRequest(Contract):
    scenario: SimulationRequest
    outage_hours: float = Field(
        ge=1 / 60,
        le=168,
        description="Test [scenario.start_utc, start + outage_hours); no profile extrapolation.",
    )
    candidate_capacities_kwh: list[Capacity] = Field(
        min_length=1, max_length=MAX_CANDIDATES
    )
    costs: ComparableCosts | None = None

    @model_validator(mode="after")
    def valid_search(self) -> Self:
        candidates = self.candidate_capacities_kwh
        if len(set(candidates)) != len(candidates):
            raise ValueError("Candidate capacities must be unique")
        if self.outage_hours > self.scenario.duration_hours:
            raise ValueError("Outage target cannot exceed scenario.duration_hours")
        count = ceil(self.outage_hours * 60 / self.scenario.step_minutes)
        if count * len(candidates) > MAX_BASE_INTERVALS:
            raise ValueError(
                "Search exceeds the 20000 base-interval computation budget"
            )
        grid = self.scenario.grid
        online = (
            any(grid.profile_online[:count])
            if grid.profile_online is not None
            else grid.online
        )
        if online:
            raise ValueError("Grid must be offline throughout the tested outage")
        if self.costs is not None:
            capacities = [entry.capacity_kwh for entry in self.costs.entries]
            if len(set(capacities)) != len(capacities):
                raise ValueError("Each cost capacity must be unique")
            if set(capacities) != set(candidates):
                raise ValueError("Costs must cover exactly the candidate capacity set")
        return self


class DesignCandidateResult(Contract):
    capacity_kwh: float
    valid: Literal[True] = True
    feasible: bool
    infeasibility_reasons: list[Literal["critical_shortfall_within_outage"]]
    cost_amount: float | None
    model_version: str
    schema_version: str
    provenance: Provenance
    simulation_run_id: str
    simulation_input_hash: str
    simulation_result_hash: str
    input: SimulationRequest
    summary: SimulationSummary
    warnings: list[str]


class DesignSearchResult(Contract):
    search_version: str = SEARCH_VERSION
    model_version: str = MODEL_VERSION
    schema_version: str = SCHEMA_VERSION
    search_id: str
    input_hash: str
    result_hash: str
    input: DesignSearchRequest
    status: Literal["feasible_candidate_found", "no_feasible_candidate"]
    selection_rule: Literal["smallest_passing_capacity_in_candidate_set"]
    selected_capacity_kwh: float | None
    selected_simulation_run_id: str | None
    physics_calls: int
    candidates: list[DesignCandidateResult]
    warnings: list[str]


def json_hash(value: dict) -> str:
    """SHA-256 of UTF-8 Python canonical JSON, also used for full trace replay."""
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    ).hexdigest()


def search_designs(request: DesignSearchRequest) -> DesignSearchResult:
    # Revalidate Python callers, including model_copy/model_construct bypasses.
    request = DesignSearchRequest.model_validate(request.model_dump(mode="json"))
    body = request.model_dump(mode="json")
    body["candidate_capacities_kwh"].sort()
    if request.costs is not None:
        body["costs"]["entries"].sort(key=lambda item: item["capacity_kwh"])
    canonical = DesignSearchRequest.model_validate(body)
    digest = json_hash(canonical.model_dump(mode="json"))

    # The target is a prefix of the validated scenario, never an extrapolation.
    scenario = canonical.scenario.model_dump(mode="json")
    scenario["duration_hours"] = canonical.outage_hours
    count = ceil(canonical.outage_hours * 60 / canonical.scenario.step_minutes)
    for owner, field in (("solar", "profile_kw"), ("grid", "profile_online")):
        if scenario[owner][field] is not None:
            scenario[owner][field] = scenario[owner][field][:count]
    costs = (
        {entry.capacity_kwh: entry.amount for entry in canonical.costs.entries}
        if canonical.costs is not None
        else {}
    )
    candidates = []
    for capacity in canonical.candidate_capacities_kwh:
        scenario["battery"]["capacity_kwh"] = capacity
        result = simulate(SimulationRequest.model_validate(scenario))
        feasible = result.summary.survived_full_window
        candidates.append(
            DesignCandidateResult(
                capacity_kwh=capacity,
                feasible=feasible,
                infeasibility_reasons=[]
                if feasible
                else ["critical_shortfall_within_outage"],
                cost_amount=costs.get(capacity),
                model_version=result.model_version,
                schema_version=result.schema_version,
                provenance=result.provenance,
                simulation_run_id=result.run_id,
                simulation_input_hash=result.input_hash,
                simulation_result_hash=json_hash(result.model_dump(mode="json")),
                input=result.input,
                summary=result.summary,
                warnings=result.warnings,
            )
        )
    # All candidates were simulated, including those above the first passing one.
    selected = next((candidate for candidate in candidates if candidate.feasible), None)
    warnings = [
        "Selection is the smallest passing capacity in the explicit candidate set; no continuous/global or market-cost optimum is claimed.",
        "Capacity changes only: inverter, charge/discharge power limits, SOC fractions and loads remain fixed. Hardware compatibility is not established.",
        "A null observed failure is horizon-censored, not infinite autonomy. Feasibility concerns critical loads only.",
    ]
    if canonical.costs is not None:
        warnings.append(
            "Costs are user-declared comparable totals, not verified quotes, and do not change capacity ranking."
        )
    if canonical.scenario.load.critical_kw == 0:
        warnings.append(
            "No critical demand was specified; critical-load survival is vacuous."
        )
    payload = {
        "search_version": SEARCH_VERSION,
        "model_version": MODEL_VERSION,
        "schema_version": SCHEMA_VERSION,
        "search_id": str(
            uuid5(
                NAMESPACE_URL,
                f"design-search:{SEARCH_VERSION}:{MODEL_VERSION}:{digest}",
            )
        ),
        "input_hash": digest,
        "input": canonical.model_dump(mode="json"),
        "status": "feasible_candidate_found" if selected else "no_feasible_candidate",
        "selection_rule": "smallest_passing_capacity_in_candidate_set",
        "selected_capacity_kwh": selected.capacity_kwh if selected else None,
        "selected_simulation_run_id": selected.simulation_run_id if selected else None,
        "physics_calls": len(candidates),
        "candidates": [candidate.model_dump(mode="json") for candidate in candidates],
        "warnings": warnings,
    }
    return DesignSearchResult(result_hash=json_hash(payload), **payload)
