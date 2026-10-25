"""Historical research preview. Imports neural/scientific packages only on use."""

from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import Field

from services.simulation.schemas import Contract

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FORECAST = ROOT / "research/energydna/artifacts/gru-v1"
EXAMPLES = ROOT / "research/energydna/examples/historical.json"
EXAMPLES_SHA256 = "fe74da34de5e17f522b3c4fbaee08115d67495e28da23a1e5ae7f2d2f1ac9c0f"


class ForecastRequest(Contract):
    example_id: Literal["rat-march20", "silvia-march20", "mouse-march20"] = (
        "rat-march20"
    )


class ForecastPreview(Contract):
    schema_version: Literal["lastlight-forecast-preview-1"] = (
        "lastlight-forecast-preview-1"
    )
    example_id: str
    building_id: str
    forecast_origin_local: str
    history_start_local: str
    timestamp_basis: str
    horizon_hours: Literal[1] = 1
    interval_hours: Literal[1] = 1
    units: Literal["whole-building average kW"] = "whole-building average kW"
    history_kw: list[float] = Field(min_length=168, max_length=168)
    recorded_actual_kw: float = Field(ge=0)
    baseline_kw: float = Field(ge=0)
    neural_kw: float | None = Field(default=None, ge=0)
    neural_status: Literal["available", "unavailable", "incompatible_checkpoint"]
    model_version: str | None = None
    preferred_method: Literal["persistence"] = "persistence"
    connected_to_physics: Literal[False] = False
    source_commit: str
    source_subset_sha256: str
    example_sha256: str
    attribution: str
    source_url: str
    license_url: str
    warnings: list[str]


@lru_cache(maxsize=3)
def load_forecaster(directory: Path, digest: str):
    from research.energydna.inference import EnergyPredictor

    return EnergyPredictor(directory)


def forecast(
    request: ForecastRequest, directory: Path = DEFAULT_FORECAST
) -> ForecastPreview:
    try:
        content = EXAMPLES.read_bytes()
    except OSError as error:
        raise HTTPException(
            503, "Packaged historical research examples are not installed"
        ) from error
    if hashlib.sha256(content).hexdigest() != EXAMPLES_SHA256:
        raise HTTPException(
            503, "Historical example checksum failed; research preview is unavailable"
        )
    package = json.loads(content)
    example = next(
        item for item in package["examples"] if item["example_id"] == request.example_id
    )
    history = example["history_kw"]
    if len(history) != 168 or any(not math.isfinite(v) or v < 0 for v in history):
        raise ValueError(
            "Packaged history must be observed finite nonnegative hourly load"
        )
    status, value, version = "unavailable", None, None
    warnings = [
        "Overseas historical whole-building research, not a measured Kyrgyz school or critical circuits.",
        "Not connected to emergency critical-load physics.",
        "One-hour rolling-origin research forecast. Persistence remains preferred by validation MAE.",
        "No calibrated forecast uncertainty interval is available. Historical target is shown only for retrospective comparison.",
    ]
    if (directory / "manifest.json").is_file():
        try:
            digest = hashlib.sha256(
                b"".join(
                    (directory / name).read_bytes()
                    for name in ["manifest.json", "model.pt", "ridge.json"]
                )
            ).hexdigest()
            predictor = load_forecaster(directory.resolve(), digest)
            import pandas as pd

            value = predictor.predict(
                history, pd.Timestamp(example["forecast_origin_local"])
            )
            status, version = "available", predictor.manifest["model_version"]
        except (ImportError, OSError):
            warnings.append(
                "Neural runtime or artifact unavailable; the observed-history persistence baseline remains available."
            )
        except (ValueError, RuntimeError, KeyError, TypeError):
            status = "incompatible_checkpoint"
            warnings.append(
                "Neural integrity/feature contract failed; persistence and physics remain available."
            )
    else:
        warnings.append(
            "Neural checkpoint missing; persistence and physics remain available."
        )
    source = package["source"]
    return ForecastPreview(
        **example,
        timestamp_basis=source["timestamp_basis"],
        baseline_kw=history[-1],
        neural_kw=value,
        neural_status=status,
        model_version=version,
        source_commit=source["source_commit"],
        source_subset_sha256=source["sha256"]["electricity.csv"],
        example_sha256=hashlib.sha256(content).hexdigest(),
        attribution=source["attribution"],
        source_url=source["source_urls"]["electricity.csv"],
        license_url=source["upstream_license"],
        warnings=warnings,
    )


def create_forecast_router() -> APIRouter:
    router = APIRouter(
        prefix="/api/v1/ml/energydna", tags=["Historical research forecasting"]
    )

    @router.post("/forecast", response_model=ForecastPreview)
    def preview(request: ForecastRequest, http: Request) -> ForecastPreview:
        directory = Path(
            getattr(http.app.state, "energydna_checkpoint_dir", DEFAULT_FORECAST)
        )
        return forecast(request, directory)

    return router
