"""Versioned research allocation proposal, explicitly unsupported by physics v1."""

from datetime import datetime, timezone
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator, model_validator
from services.simulation.schemas import Contract, Power


class ForecastSeries(Contract):
    contract_version: Literal["lastlight-forecast-allocation-research-1"] = (
        "lastlight-forecast-allocation-research-1"
    )
    source_building_id: str = Field(min_length=1, max_length=200)
    source_references: list[str] = Field(min_length=1, max_length=30)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    model_version: str = Field(min_length=1)
    forecast_origin: datetime
    source_timezone: str
    horizon_hours: int = Field(ge=1, le=24)
    interval_minutes: Literal[60] = 60
    units: Literal["average_kw"] = "average_kw"
    whole_building_kw: list[Power] = Field(min_length=1, max_length=24)
    lower_kw: list[Power] | None = None
    upper_kw: list[Power] | None = None
    missing_data_policy: str = Field(min_length=1)
    critical_fraction: float = Field(ge=0, le=1)
    allocation_evidence: str = Field(min_length=1)
    allocation_reviewer: str = Field(min_length=1)

    @field_validator("forecast_origin")
    @classmethod
    def aware_origin(cls, value):
        if value.utcoffset() is None:
            raise ValueError(
                "Reviewed timezone-aware forecast origin required; do not guess BDG2 local DST"
            )
        return value.astimezone(timezone.utc)

    @field_validator("source_timezone")
    @classmethod
    def known_zone(cls, value):
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("Known IANA source timezone required") from error
        return value

    @model_validator(mode="after")
    def complete_profile(self):
        if len(self.whole_building_kw) != self.horizon_hours:
            raise ValueError(
                "Complete hourly horizon required; missing forecasts are never silently filled"
            )
        if (self.lower_kw is None) != (self.upper_kw is None):
            raise ValueError("Both uncertainty bounds or neither required")
        if self.lower_kw is not None:
            if (
                len(self.lower_kw) != self.horizon_hours
                or len(self.upper_kw) != self.horizon_hours
            ):
                raise ValueError("Uncertainty must cover every forecast interval")
            if any(
                not lo <= value <= hi
                for lo, value, hi in zip(
                    self.lower_kw, self.whole_building_kw, self.upper_kw, strict=True
                )
            ):
                raise ValueError("Uncertainty bounds must contain point forecasts")
        return self


def allocate_research(series: ForecastSeries) -> dict:
    series = ForecastSeries.model_validate(series.model_dump())
    critical = [value * series.critical_fraction for value in series.whole_building_kw]
    noncritical = [
        value - c for value, c in zip(series.whole_building_kw, critical, strict=True)
    ]
    return {
        "contract_version": series.contract_version,
        "source": series.model_dump(mode="json"),
        "critical_kw": critical,
        "noncritical_kw": noncritical,
        "total_energy_kwh": sum(series.whole_building_kw),
        "conversion": "hourly average kW × 1 h = interval kWh",
        "uncertainty_available": series.lower_kw is not None,
        "engineering_clearance": False,
        "official_v1_dynamic_load_compatible": False,
        "warnings": [
            "Allocation fraction requires actual circuit evidence; a user-supplied reviewer name is not verified engineering approval.",
            "The original one-hour checkpoint has no calibrated uncertainty interval.",
            "Official v1 has constant critical/noncritical loads. No forecast profile is injected.",
        ],
    }


def to_official_v1(_series: ForecastSeries):
    raise ValueError(
        "Official schema 1.0.0 cannot accept dynamic load profiles; a versioned owner-reviewed engine extension is required"
    )
