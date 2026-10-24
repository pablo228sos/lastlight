"""Working demand baselines only; these are estimates, not resilience results."""

from datetime import timedelta
import hashlib
import json
from pathlib import Path
from typing import Literal
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator, model_validator

from .schemas import Contract, Power, Provenance, SimulationRequest


class ForecastRequest(Contract):
    mode: Literal["cold_start", "historical"]
    start_utc: str = "2026-01-01T00:00:00Z"
    hours: int = Field(default=24, ge=1, le=24)
    history_kw: list[Power] | None = Field(
        default=None, min_length=168, max_length=8760
    )
    primary_use: str = Field(default="unknown", max_length=100)
    local_timezone: str = Field(default="UTC", max_length=100)
    seed: int = Field(default=0, ge=0, le=2**32 - 1)

    @field_validator("start_utc")
    @classmethod
    def timestamp(cls, value):
        return (
            SimulationRequest.parse_timestamp(value).isoformat().replace("+00:00", "Z")
        )

    @field_validator("local_timezone")
    @classmethod
    def zone(cls, value):
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("Unknown IANA timezone") from error
        return value

    @model_validator(mode="after")
    def history_required(self):
        if self.mode == "historical" and self.history_kw is None:
            raise ValueError(
                "Historical mode requires contiguous hourly history immediately before start_utc"
            )
        if self.mode == "cold_start" and self.history_kw is not None:
            raise ValueError("Cold start must not consume building history")
        return self


class ForecastPoint(Contract):
    t_utc: str
    demand_kw: float


class ForecastSummary(Contract):
    mode: str
    hours: int
    units: str = "whole-building average kW"
    neural_model: bool = False


class ForecastResult(Contract):
    run_id: str
    input_hash: str
    physics_version: None = None
    model_version: str
    seed: int
    assumptions: list[str]
    provenance: Provenance
    summary: ForecastSummary
    trace: list[ForecastPoint]
    warnings: list[str]


def forecast(request: ForecastRequest) -> ForecastResult:
    from ml.models.energy_dna import (
        BASELINE_VERSION,
        forecast_cold_start,
        forecast_historical,
    )

    start = SimulationRequest.parse_timestamp(request.start_utc)
    model_version = BASELINE_VERSION
    if request.mode == "historical":
        values = forecast_historical(request.history_kw, request.hours)
    else:
        path = (
            Path(__file__).resolve().parents[2]
            / "ml/artifacts/energy-dna-baseline/profiles.json"
        )
        profile = json.loads(path.read_text(encoding="utf8"))
        values = forecast_cold_start(
            profile, request.primary_use, start, request.local_timezone, request.hours
        )
        canonical = json.dumps(profile, sort_keys=True, separators=(",", ":"), allow_nan=False)
        model_version += "-" + hashlib.sha256(canonical.encode()).hexdigest()[:12]
    digest = hashlib.sha256(request.model_dump_json().encode()).hexdigest()
    return ForecastResult(
        run_id=str(uuid5(NAMESPACE_URL, f"{model_version}:{digest}")),
        input_hash=digest,
        model_version=model_version,
        seed=request.seed,
        assumptions=[
            "Hourly energy converted to average kW. No neural demand model.",
            "Historical mode: last-week same hour; history is contiguous and ends immediately before start.",
            "Cold start: category/hour profile fitted only on overseas research training buildings.",
        ],
        provenance=Provenance(
            category="research_derived",
            references=["https://github.com/buds-lab/building-data-genome-project-2"],
        ),
        summary=ForecastSummary(mode=request.mode, hours=request.hours),
        trace=[
            ForecastPoint(
                t_utc=(start + timedelta(hours=i)).isoformat().replace("+00:00", "Z"),
                demand_kw=float(value),
            )
            for i, value in enumerate(values)
        ],
        warnings=[
            "Demand estimate only; not a measured Kyrgyzstan building or an engineering safety result.",
            "Critical/noncritical allocation must be explicitly supplied before physics dispatch.",
        ],
    )
