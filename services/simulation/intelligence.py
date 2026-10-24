"""Strict API envelopes; imports/training are separate from deterministic dispatch."""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

from pydantic import Field, model_validator

from .engine import simulate
from .schemas import Contract, SimulationRequest, SimulationResult, Provenance


class FragilityEstimate(Contract):
    model_version: str
    synthetic_failure_score: float
    predicted_failure: bool
    baseline_failure_score: float
    outside_training_domain: bool
    high_uncertainty: bool
    physics_required: bool
    engineering_clearance: bool
    warnings: list[str]


class PredictionResult(SimulationResult):
    model_version: str | None
    physics_run_id: str
    physics_verified: Literal[True] = True
    engineering_clearance: Literal[False] = False
    estimate: FragilityEstimate | None


class FrontierRequest(Contract):
    scenario: SimulationRequest = Field(
        default_factory=lambda: SimulationRequest(duration_hours=24)
    )
    soc_points: int = Field(default=13, ge=3, le=41)
    duration_points: int = Field(default=21, ge=3, le=49)
    maximum_hours: float = Field(default=24, ge=0.25, le=48)
    include_ml: bool = False

    @model_validator(mode="after")
    def budget(self):
        if self.soc_points * self.duration_points > 1600:
            raise ValueError("Frontier exceeds 1600-cell budget")
        for profile in [
            self.scenario.solar.profile_kw,
            self.scenario.grid.profile_online,
            self.scenario.load.critical_profile_kw,
            self.scenario.load.noncritical_profile_kw,
        ]:
            if (
                profile is not None
                and self.maximum_hours > self.scenario.duration_hours
            ):
                raise ValueError("No extrapolation of supplied profiles")
        return self


class FrontierCell(Contract):
    initial_soc: float
    duration_hours: float
    failed: bool
    first_failure_hours: float | None
    physics_verified: bool
    verification_run_id: str


class FrontierEstimate(Contract):
    initial_soc: float
    duration_hours: float
    synthetic_failure_score: float
    physics_verified: bool
    outside_training_domain: bool


class VerifiedCandidate(FrontierEstimate):
    failed: bool
    run_id: str


class FrontierSummary(Contract):
    physics_calls: int
    verified_cells: int
    method: str


class FrontierResult(Contract):
    run_id: str
    physics_version: str
    model_version: str | None
    input_hash: str
    seed: int
    assumptions: list[str]
    provenance: Provenance
    summary: FrontierSummary
    trace: list[FrontierCell]
    ml_estimates: list[FrontierEstimate]
    verified_candidates: list[VerifiedCandidate]
    warnings: list[str]


@lru_cache(maxsize=1)
def predictor():
    from ml.models.fragility_net import FragilityPredictor

    directory = Path(__file__).resolve().parents[2] / "ml/artifacts/fragility-v1"
    return FragilityPredictor.load(directory)


def predict_verified(request: SimulationRequest) -> PredictionResult:
    physics = simulate(request)
    estimate = None
    warnings = []
    try:
        estimate = FragilityEstimate.model_validate(predictor().predict(request))
    except (OSError, ValueError, ImportError, RuntimeError, KeyError) as error:
        warnings.append(
            f"ML unavailable ({type(error).__name__}); authoritative physics evaluation used."
        )
    model_version = estimate.model_version if estimate else None
    payload = physics.model_dump()
    payload.update(
        run_id=str(uuid5(NAMESPACE_URL, f"fragility:{physics.run_id}:{model_version}")),
        physics_run_id=physics.run_id,
        model_version=model_version,
        estimate=estimate,
        warnings=physics.warnings + warnings,
    )
    return PredictionResult.model_validate(payload)
