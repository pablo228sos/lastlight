"""Bounded deterministic battery sizing using the OFFICIAL v1 physics simulator.

No second dispatch/analytical approximation: every listed capacity executes simulate().
Survival means no observed critical shortfall on the exclusive [0, target) horizon.
"""

from __future__ import annotations

import hashlib
import json
from typing import Self
from uuid import NAMESPACE_URL, uuid5

from pydantic import Field, model_validator

from . import MODEL_VERSION, SCHEMA_VERSION
from .engine import simulate
from .schemas import Contract, Provenance, SimulationRequest


class ComparableCost(Contract):
    """User-entered comparable amount, not a market quote or cost optimization."""

    capacity_kwh: float = Field(ge=0.001, le=20_000)
    amount: float = Field(ge=0, le=1_000_000_000_000)
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    basis: str = Field(min_length=1, max_length=120)


class DesignSearchRequest(Contract):
    scenario: SimulationRequest
    outage_target_hours: float = Field(gt=0, le=168)
    candidate_capacities_kwh: list[float] = Field(min_length=1, max_length=32)
    comparable_costs: list[ComparableCost] | None = Field(default=None, max_length=32)

    @model_validator(mode="after")
    def validate_search(self) -> Self:
        # Explicit target = tested duration, not analytic extrapolation. The client
        # may choose a different target by supplying a matching scenario duration.
        if self.outage_target_hours != self.scenario.duration_hours:
            raise ValueError(
                "outage_target_hours must equal scenario.duration_hours; "
                "the complete tested horizon must be explicit"
            )
        if self.scenario.grid.online or (
            self.scenario.grid.profile_online is not None
            and any(self.scenario.grid.profile_online)
        ):
            raise ValueError(
                "the defined outage requires grid offline for every tested interval"
            )
        if self.scenario.interval_count * len(self.candidate_capacities_kwh) > 20_000:
            raise ValueError("design search exceeds the 20,000-interval work budget")
        for capacity in self.candidate_capacities_kwh:
            if not 0.001 <= capacity <= 20_000:
                raise ValueError("candidate capacities must be in 0.001..20000 kWh")
        if len(set(self.candidate_capacities_kwh)) != len(
            self.candidate_capacities_kwh
        ):
            raise ValueError("candidate capacities must be unique")
        costs = self.comparable_costs
        if costs is not None:
            if len(costs) != len(self.candidate_capacities_kwh):
                raise ValueError(
                    "comparable_costs must cover every candidate exactly once"
                )
            if {c.capacity_kwh for c in costs} != set(self.candidate_capacities_kwh):
                raise ValueError(
                    "cost capacities must match the explicit candidate set"
                )
            if len({(c.currency, c.basis) for c in costs}) != 1:
                raise ValueError("all comparable costs must share currency and basis")
        return self


class DesignCandidateResult(Contract):
    capacity_kwh: float
    valid: bool
    survived_target: bool
    first_critical_failure_hours: float | None
    first_critical_failure_utc: str | None
    unserved_critical_kwh: float
    ending_soc: float
    infeasibility_reasons: list[str]
    physics_run_id: str
    physics_input_hash: str
    comparable_cost: ComparableCost | None = None


class DesignSearchResult(Contract):
    schema_version: str = SCHEMA_VERSION
    physics_model_version: str = MODEL_VERSION
    run_id: str
    input_hash: str
    result_hash: str
    seed: int
    outage_target_hours: float
    provenance: Provenance
    candidate_count: int
    selected_capacity_kwh: float | None
    selection_rule: str
    physics_verified: bool
    candidates: list[DesignCandidateResult]
    warnings: list[str]


def _digest(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def design_search(request: DesignSearchRequest) -> DesignSearchResult:
    """Rank ONLY supplied capacities; use one unchanged official simulation each."""
    s = DesignSearchRequest.model_validate(request.model_dump(mode="json"))
    capacities = sorted(s.candidate_capacities_kwh)
    costs = (
        {item.capacity_kwh: item for item in s.comparable_costs}
        if s.comparable_costs is not None
        else {}
    )
    identity = {
        "scenario": s.scenario.model_dump(mode="json"),
        "outage_target_hours": s.outage_target_hours,
        "candidate_capacities_kwh": capacities,
        "comparable_costs": [
            costs[capacity].model_dump(mode="json") for capacity in capacities
        ]
        if costs
        else None,
    }
    digest = _digest(identity)
    results = []
    for capacity in capacities:
        # Only capacity changes; SOC limits, inverter, loads, PV, grid, and seed
        # are identical. The original simulator validates all copied inputs.
        candidate = s.scenario.model_copy(
            update={
                "battery": s.scenario.battery.model_copy(
                    update={"capacity_kwh": capacity}
                )
            }
        )
        physics = simulate(candidate)
        summary = physics.summary
        survived = summary.survived_full_window
        reasons = []
        if not survived:
            reasons.append("critical_energy_unserved_during_target")
            if not candidate.inverter.islanding_capable:
                reasons.append("inverter_islanding_disabled")
            if candidate.inverter.max_kw < candidate.load.critical_kw:
                reasons.append("inverter_limit_below_critical_load")
        results.append(
            DesignCandidateResult(
                capacity_kwh=capacity,
                valid=True,
                survived_target=survived,
                first_critical_failure_hours=summary.critical_survival_hours,
                first_critical_failure_utc=summary.first_failure_utc,
                unserved_critical_kwh=summary.unserved_critical_kwh,
                ending_soc=summary.ending_soc,
                infeasibility_reasons=reasons,
                physics_run_id=physics.run_id,
                physics_input_hash=physics.input_hash,
                comparable_cost=costs.get(capacity),
            )
        )
    winner = next((x.capacity_kwh for x in results if x.survived_target), None)
    result_payload = [item.model_dump(mode="json") for item in results]
    return DesignSearchResult(
        run_id=str(uuid5(NAMESPACE_URL, f"design-search:{MODEL_VERSION}:{digest}")),
        input_hash=digest,
        result_hash=_digest(result_payload),
        seed=s.scenario.seed,
        outage_target_hours=s.outage_target_hours,
        provenance=s.scenario.provenance,
        candidate_count=len(results),
        selected_capacity_kwh=winner,
        selection_rule="smallest passing capacity within the explicit supplied set",
        physics_verified=True,
        candidates=results,
        warnings=[
            "A pass is censored at the exclusive outage horizon; it does not "
            "prove survival beyond the tested interval.",
            "Selection minimizes capacity within supplied candidates, NOT price "
            "or global capacity; costs are user-provided annotations only.",
        ],
    )
