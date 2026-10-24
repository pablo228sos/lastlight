"""Version 1 wire contracts. Power is AC-side kW; stored energy is DC kWh."""

from __future__ import annotations

from datetime import datetime, timezone
from math import ceil
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from . import MODEL_VERSION, SCHEMA_VERSION

Power = Annotated[float, Field(ge=0, le=50_000)]
Fraction = Annotated[float, Field(ge=0, le=1)]
Efficiency = Annotated[float, Field(ge=0.01, le=1)]


class Contract(BaseModel):
    model_config = ConfigDict(
        extra="forbid", allow_inf_nan=False, strict=True, validate_default=True
    )


class Battery(Contract):
    capacity_kwh: float = Field(default=24, ge=0.001, le=20_000)
    initial_soc: Fraction = 0.8
    minimum_soc: Fraction = 0.2
    maximum_soc: Fraction = 1.0
    charge_efficiency: Efficiency = 0.95
    discharge_efficiency: Efficiency = 0.95
    max_charge_kw: Power = 6.0
    max_discharge_kw: Power = 8.0

    @model_validator(mode="after")
    def ordered_soc(self) -> Self:
        if not self.minimum_soc <= self.initial_soc <= self.maximum_soc:
            raise ValueError(
                "SOC must satisfy minimum_soc <= initial_soc <= maximum_soc"
            )
        if self.minimum_soc >= self.maximum_soc:
            raise ValueError("minimum_soc must be less than maximum_soc")
        return self


class Inverter(Contract):
    max_kw: Power = 8.0
    islanding_capable: bool = True


class Load(Contract):
    critical_kw: Power = 1.5
    noncritical_kw: Power = 2.0
    shed_noncritical_during_outage: bool = True


class Solar(Contract):
    generation_kw: Power = 0.0
    profile_kw: list[Power] | None = Field(default=None, max_length=10_080)
    islanding_capable: bool = False


class Grid(Contract):
    online: bool = False
    profile_online: list[bool] | None = Field(default=None, max_length=10_080)
    import_limit_kw: Power = 50.0
    charge_battery: bool = False


class Provenance(Contract):
    category: Literal["measured", "research_derived", "synthetic"] = "synthetic"
    references: list[Annotated[str, Field(min_length=1, max_length=500)]] = Field(
        default_factory=lambda: ["docs/physics/MODEL.md"], max_length=30
    )


class SimulationRequest(Contract):
    start_utc: datetime = Field(
        default=datetime(2026, 1, 1, tzinfo=timezone.utc),
        description="Timezone-aware ISO 8601 time; normalized to UTC. Fixed default for replay.",
    )
    duration_hours: float = Field(default=12, ge=1 / 60, le=168)
    step_minutes: int = Field(default=15, ge=1, le=60)
    seed: int = Field(default=0, ge=0, le=2**32 - 1)
    battery: Battery = Field(default_factory=Battery)
    inverter: Inverter = Field(default_factory=Inverter)
    load: Load = Field(default_factory=Load)
    solar: Solar = Field(default_factory=Solar)
    grid: Grid = Field(default_factory=Grid)
    provenance: Provenance = Field(default_factory=Provenance)

    @field_validator("start_utc", mode="before")
    @classmethod
    def parse_timestamp(cls, value: object) -> datetime:
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise ValueError(
                "start_utc must include a timezone (Z or an explicit UTC offset)"
            )
        value = value.astimezone(timezone.utc)
        if not 1970 <= value.year <= 2099:
            raise ValueError("start_utc must be in years 1970..2099")
        return value

    @model_validator(mode="after")
    def profile_lengths(self) -> Self:
        for name, profile in [
            ("solar.profile_kw", self.solar.profile_kw),
            ("grid.profile_online", self.grid.profile_online),
        ]:
            if profile is not None and len(profile) != self.interval_count:
                raise ValueError(
                    f"{name} must have exactly {self.interval_count} entries"
                )
        return self

    @property
    def interval_count(self) -> int:
        return ceil(self.duration_hours * 60 / self.step_minutes)


class SimulationTracePoint(Contract):
    # Existing apps/web/src/lib/contracts.ts fields are preserved without renaming.
    t_utc: str
    grid_kw: float
    solar_kw: float
    battery_charge_kw: float
    battery_discharge_kw: float
    battery_soc: float
    critical_served_kw: float
    critical_demand_kw: float
    noncritical_served_kw: float
    unserved_critical_kw: float
    status: Literal["normal", "islanded", "degraded", "critical_failure"]
    # Additive interval/energy accounting fields proposed to the frontend owner.
    t_end_utc: str
    elapsed_hours: float
    duration_hours: float
    grid_online: bool
    solar_available_kw: float
    solar_curtailed_kw: float
    grid_charge_kw: float
    noncritical_demand_kw: float
    unserved_noncritical_kw: float
    battery_soc_end: float
    battery_energy_kwh: float
    battery_energy_end_kwh: float
    conversion_loss_kwh: float
    ac_balance_residual_kwh: float
    storage_balance_residual_kwh: float
    balance_residual_kwh: float


class SimulationSummary(Contract):
    critical_survival_hours: float | None
    served_critical_fraction: float
    unserved_critical_kwh: float
    first_failure_utc: str | None
    max_balance_residual_kwh: float
    observed_duration_hours: float
    survived_full_window: bool
    idealized_autonomy_hours: float | None
    total_critical_demand_kwh: float
    served_critical_kwh: float
    served_noncritical_kwh: float
    unserved_noncritical_kwh: float
    grid_import_kwh: float
    solar_available_kwh: float
    solar_used_kwh: float
    solar_curtailed_kwh: float
    battery_charge_kwh: float
    battery_discharge_kwh: float
    conversion_loss_kwh: float
    initial_battery_energy_kwh: float
    final_battery_energy_kwh: float
    usable_capacity_kwh: float
    ending_soc: float
    cumulative_balance_residual_kwh: float


class SimulationResult(Contract):
    run_id: str
    model_version: str = MODEL_VERSION
    input_hash: str
    seed: int
    summary: SimulationSummary
    trace: list[SimulationTracePoint]
    provenance: Provenance
    schema_version: str = SCHEMA_VERSION
    input: SimulationRequest
    warnings: list[str]


class ComparisonRequest(Contract):
    baseline: SimulationRequest = Field(default_factory=SimulationRequest)
    upgrade: Literal["battery_36_kwh", "full_precharge"] = "battery_36_kwh"

    @model_validator(mode="after")
    def approved_upgrade(self) -> Self:
        if (
            self.upgrade == "battery_36_kwh"
            and self.baseline.battery.capacity_kwh >= 36
        ):
            raise ValueError("battery_36_kwh requires baseline capacity below 36 kWh")
        if self.upgrade == "full_precharge" and self.baseline.battery.maximum_soc != 1:
            raise ValueError("full_precharge requires maximum_soc = 1")
        return self


class ComparisonDelta(Contract):
    served_critical_kwh: float
    unserved_critical_kwh: float
    critical_survival_hours: float | None
    idealized_autonomy_hours: float | None


class ComparisonResult(Contract):
    schema_version: str = SCHEMA_VERSION
    upgrade: Literal["battery_36_kwh", "full_precharge"]
    baseline: SimulationResult
    upgraded: SimulationResult
    delta: ComparisonDelta


class ErrorDetail(Contract):
    location: list[str | int]
    message: str
    type: str


class ErrorBody(Contract):
    code: str
    message: str
    details: list[ErrorDetail]


class ErrorResponse(Contract):
    error: ErrorBody


class Health(Contract):
    status: Literal["ok"] = "ok"
    model_version: str = MODEL_VERSION
    schema_version: str = SCHEMA_VERSION
