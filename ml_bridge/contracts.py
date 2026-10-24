"""Additive bridge envelope; the official result remains nested and unmodified."""

from typing import Literal

from pydantic import Field, model_validator

from services.simulation.schemas import (
    Contract,
    SimulationRequest,
    SimulationResult,
    SimulationSummary,
)
from .features import FEATURE_SCHEMA


class AssessmentRequest(Contract):
    scenario: SimulationRequest
    physics_version: Literal["lastlight-dispatch-1.0.0"] = "lastlight-dispatch-1.0.0"
    schema_version: Literal["1.0.0"] = "1.0.0"
    feature_schema: Literal["lastlight-official-v1-features-1"] = FEATURE_SCHEMA


class NeuralEstimate(Contract):
    predicted_failure: bool
    synthetic_failure_score: float = Field(ge=0, le=1)
    outside_training_domain: bool
    high_uncertainty: bool
    physics_required: Literal[True] = True
    engineering_clearance: Literal[False] = False


class NeuralAnalysis(Contract):
    status: Literal["available", "unavailable", "incompatible_checkpoint"]
    model_version: str | None = None
    feature_schema: str = FEATURE_SCHEMA
    source_physics_version: str | None = None
    estimate: NeuralEstimate | None = None
    warnings: list[str]


class Assessment(Contract):
    bridge_schema_version: Literal["lastlight-ml-bridge-1"] = "lastlight-ml-bridge-1"
    physics: SimulationResult
    neural: NeuralAnalysis
    physics_authoritative: Literal[True] = True
    engineering_clearance: Literal[False] = False


class CandidatePoint(Contract):
    initial_soc: float = Field(ge=0, le=1)
    duration_hours: float = Field(ge=1 / 60, le=48)


class CandidateRequest(AssessmentRequest):
    points: list[CandidatePoint] = Field(min_length=1, max_length=1600)
    limit: int = Field(default=12, ge=1, le=12)

    @model_validator(mode="after")
    def supported_points(self):
        pairs = {(point.initial_soc, point.duration_hours) for point in self.points}
        if len(pairs) != len(self.points):
            raise ValueError("Candidate grid points must be unique")
        for point in self.points:
            if (
                not self.scenario.battery.minimum_soc
                <= point.initial_soc
                <= self.scenario.battery.maximum_soc
            ):
                raise ValueError(
                    "Candidate charge is outside the official battery bounds"
                )
            if point.duration_hours > self.scenario.duration_hours and (
                self.scenario.solar.profile_kw is not None
                or self.scenario.grid.profile_online is not None
            ):
                raise ValueError("Candidate grid cannot extrapolate supplied profiles")
        return self


class VerifiedCandidate(CandidatePoint):
    neural: NeuralEstimate
    physics_verified: Literal[True] = True
    physics_model_version: Literal["lastlight-dispatch-1.0.0"] = (
        "lastlight-dispatch-1.0.0"
    )
    physics_schema_version: Literal["1.0.0"] = "1.0.0"
    physics_run_id: str
    input_hash: str
    physics_summary: SimulationSummary
    warnings: list[str]


class CandidateResult(Contract):
    bridge_schema_version: Literal["lastlight-ml-bridge-1"] = "lastlight-ml-bridge-1"
    physics_version: Literal["lastlight-dispatch-1.0.0"] = "lastlight-dispatch-1.0.0"
    schema_version: Literal["1.0.0"] = "1.0.0"
    neural_status: Literal["available", "unavailable", "incompatible_checkpoint"]
    neural_model_version: str | None
    candidates: list[VerifiedCandidate]
    warnings: list[str]
