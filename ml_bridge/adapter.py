"""Run unchanged official physics first; neural inference is optional and separate."""

from functools import lru_cache
from pathlib import Path

from services.simulation.engine import simulate
from .contracts import Assessment, AssessmentRequest, NeuralAnalysis
from .runtime import source_identity

DEFAULT_CHECKPOINT = Path(__file__).parent / "artifacts/fragility-official-v1"
SCORE_WARNING = "Neural scores describe synthetic simulation labels, not real-world grid-outage probabilities or equipment approval."


@lru_cache(maxsize=4)
def predictor(directory: Path, source_sha256: str):
    from .inference import FragilityPredictor

    return FragilityPredictor.load(directory)


def analyze_neural(scenario, checkpoint_dir: Path) -> NeuralAnalysis:
    if not (checkpoint_dir / "manifest.json").is_file():
        return NeuralAnalysis(
            status="unavailable",
            warnings=[
                SCORE_WARNING,
                "No matching neural checkpoint is installed; official physics remains available.",
            ],
        )
    try:
        identity = source_identity()
        model = predictor(checkpoint_dir.resolve(), identity["source_sha256"])
        estimate, warnings = model.predict(scenario)
        return NeuralAnalysis(
            status="available",
            model_version=model.manifest["model_version"],
            source_physics_version=model.manifest["physics_version"],
            estimate=estimate,
            warnings=[SCORE_WARNING, *warnings],
        )
    except (ImportError, OSError):
        return NeuralAnalysis(
            status="unavailable",
            warnings=[
                SCORE_WARNING,
                "Neural runtime/checkpoint is unavailable; use the official physics result.",
            ],
        )
    except (ValueError, RuntimeError, KeyError, TypeError):
        return NeuralAnalysis(
            status="incompatible_checkpoint",
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
        physics=physics, neural=analyze_neural(request.scenario, checkpoint_dir)
    )
