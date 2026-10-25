"""Run unchanged official physics first; neural inference is optional and separate."""

from functools import lru_cache
import hashlib
from pathlib import Path

from services.simulation.engine import simulate
from .contracts import Assessment, AssessmentRequest, NeuralAnalysis
from .runtime import source_identity

DEFAULT_CHECKPOINT = Path(__file__).parent / "artifacts/fragility-official-v1"
SCORE_WARNING = "Neural scores describe synthetic simulation labels, not real-world grid-outage probabilities or equipment approval."


@lru_cache(maxsize=4)
def _predictor(directory: Path, source_sha256: str, checkpoint_sha256: str):
    from .inference import FragilityPredictor

    return FragilityPredictor.load(directory)


def predictor(directory: Path, source_sha256: str):
    # File bytes, rather than timestamps, invalidate a warm model when deployment
    # artifacts change. The loader still performs all catalog/source checks.
    digest = hashlib.sha256()
    for path in [
        directory / "manifest.json",
        directory / "model.pt",
        Path(__file__).parent / "verified_catalog.json",
    ]:
        digest.update(path.read_bytes())
    return _predictor(directory, source_sha256, digest.hexdigest())


def analyze_neural(
    scenario, checkpoint_dir: Path, expected_feature_schema=None
) -> NeuralAnalysis:
    if not (checkpoint_dir / "manifest.json").is_file():
        return NeuralAnalysis(
            status="unavailable",
            feature_schema=expected_feature_schema
            or "lastlight-official-v1-features-1",
            warnings=[
                SCORE_WARNING,
                "No matching neural checkpoint is installed; official physics remains available.",
            ],
        )
    try:
        identity = source_identity()
        model = predictor(checkpoint_dir.resolve(), identity["source_sha256"])
        if (
            expected_feature_schema is not None
            and model.manifest["feature_schema"] != expected_feature_schema
        ):
            raise ValueError("Requested feature contract differs from checkpoint")
        estimate, warnings = model.predict(scenario)
        return NeuralAnalysis(
            status="available",
            model_version=model.manifest["model_version"],
            feature_schema=model.manifest["feature_schema"],
            source_physics_version=model.manifest["physics_version"],
            estimate=estimate,
            warnings=[SCORE_WARNING, *warnings],
        )
    except (ImportError, OSError):
        return NeuralAnalysis(
            status="unavailable",
            feature_schema=expected_feature_schema
            or "lastlight-official-v1-features-1",
            warnings=[
                SCORE_WARNING,
                "Neural runtime/checkpoint is unavailable; use the official physics result.",
            ],
        )
    except (ValueError, RuntimeError, KeyError, TypeError):
        return NeuralAnalysis(
            status="incompatible_checkpoint",
            feature_schema=expected_feature_schema
            or "lastlight-official-v1-features-1",
            warnings=[
                SCORE_WARNING,
                "Checkpoint failed its version, feature, source or integrity checks; use the official physics result.",
            ],
        )


def assess(
    request: AssessmentRequest, checkpoint_dir: Path = DEFAULT_CHECKPOINT
) -> Assessment:
    request = AssessmentRequest.model_validate(request.model_dump())
    source_identity()
    physics = simulate(request.scenario)
    return Assessment(
        physics=physics,
        neural=analyze_neural(request.scenario, checkpoint_dir, request.feature_schema),
    )
