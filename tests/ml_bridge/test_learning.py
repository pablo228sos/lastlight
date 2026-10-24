import json
from pathlib import Path
import shutil

import numpy as np
import pytest

from ml_bridge.adapter import DEFAULT_CHECKPOINT, assess
from ml_bridge.contracts import AssessmentRequest
from ml_bridge.features import features
from ml_bridge.generate import generate_dataset
from ml_bridge.inference import FragilityPredictor
from ml_bridge.train import train
from services.simulation.schemas import SimulationRequest


def test_released_model_is_real_repeatable_and_separate_from_official_physics():
    request = AssessmentRequest(scenario=SimulationRequest(duration_hours=16))
    one, two = assess(request), assess(request)
    assert one == two
    assert one.neural.status == "available"
    assert one.neural.model_version.startswith("fragility-official-v1-")
    assert one.physics.model_version == "lastlight-dispatch-1.0.0"
    assert one.physics.summary.critical_survival_hours == 9.12
    assert 0 <= one.neural.estimate.synthetic_failure_score <= 1
    assert one.neural.estimate.physics_required is True


@pytest.mark.parametrize(
    "change", ["physics", "schema", "feature", "normalization", "source", "weights"]
)
def test_incompatible_checkpoint_never_removes_official_physics(tmp_path, change):
    directory = tmp_path / change
    shutil.copytree(DEFAULT_CHECKPOINT, directory)
    path = directory / "manifest.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    if change == "weights":
        (directory / "model.pt").write_bytes(b"corrupt checkpoint")
    else:
        key, value = {
            "physics": ("physics_version", "lastlight-dispatch-1.1.0"),
            "schema": ("schema_version", "1.1.0"),
            "feature": ("feature_schema", "input-statistics-1"),
            "normalization": ("scale", [1.0]),
            "source": ("source_sha256", "0" * 64),
        }[change]
        meta[key] = value
        path.write_text(json.dumps(meta), encoding="utf-8")
    result = assess(
        AssessmentRequest(scenario=SimulationRequest(duration_hours=16)), directory
    )
    assert result.neural.status == "incompatible_checkpoint"
    assert result.neural.estimate is None
    assert result.physics.summary.critical_survival_hours == 9.12


def test_training_is_reproducible_and_normalization_uses_train_only(tmp_path: Path):
    data = generate_dataset(300, seed=7)
    assert data.physical_signature.is_unique
    capacities = {name: set(rows.capacity_kwh) for name, rows in data.groupby("split")}
    assert not any(
        capacities[a] & capacities[b] for a in capacities for b in capacities if a != b
    )
    for text in data.parameters_json:
        assert SimulationRequest.model_validate_json(text).load.critical_kw >= 0
    one, two = tmp_path / "one", tmp_path / "two"
    train(data, one, seed=7, max_epochs=3)
    train(data, two, seed=7, max_epochs=3)
    first = json.loads((one / "manifest.json").read_text(encoding="utf-8"))
    second = json.loads((two / "manifest.json").read_text(encoding="utf-8"))
    assert first["checkpoint_sha256"] == second["checkpoint_sha256"]
    assert np.allclose(
        first["mean"], np.stack(data[data.split == "train"].features).mean(axis=0)
    )
    model = FragilityPredictor.load(one, require_catalog=False)
    assert np.isfinite(model.scores(features(SimulationRequest()))).all()
    # A newly trained checkpoint is not implicitly approved for production inference.
    with pytest.raises(ValueError, match="catalog"):
        FragilityPredictor.load(one)
