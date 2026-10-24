import numpy as np
import pandas as pd
import pytest

from ml.data.generate_scenarios import generate_dataset
from ml.models.fragility_net import FragilityPredictor
from ml.training.train_fragility import train


def test_generation_replay_splits_and_parquet(tmp_path):
    a = generate_dataset(240, seed=42)
    b = generate_dataset(240, seed=42)
    pd.testing.assert_frame_equal(a, b)
    assert a.scenario_id.is_unique
    assert a.input_hash.is_unique
    groups = {split: set(rows.equipment_id) for split, rows in a.groupby("split")}
    for left in groups:
        for right in groups:
            if left != right:
                assert groups[left].isdisjoint(groups[right])
    assert set(a.split) == {"train", "validation", "test", "generalization"}
    assert a.failed.nunique() == 2
    path = tmp_path / "scenarios.parquet"
    a.to_parquet(path, index=False)
    assert len(pd.read_parquet(path)) == 240


def test_real_training_checkpoint_and_inference(tmp_path):
    data = generate_dataset(480, seed=7)
    report = train(data, tmp_path, seed=7, max_epochs=8)
    assert "baseline" in report["test"] and "fragility_net" in report["test"]
    assert report["test"]["fragility_net"]["confusion_matrix"]
    assert (tmp_path / "model.pt").stat().st_size > 1000
    model = FragilityPredictor.load(tmp_path)
    vector = np.array(data[data.split == "test"].iloc[0].features)
    first = model.predict_features(vector)
    assert first == model.predict_features(vector)
    assert 0 <= first["synthetic_failure_score"] <= 1
    assert first["engineering_clearance"] is False
    assert model.predict_features(vector * 1e8)["physics_required"] is True
    second = tmp_path / "repeat"
    train(data, second, seed=7, max_epochs=8)
    assert model.predict_features(vector) == FragilityPredictor.load(
        second
    ).predict_features(vector)
    with pytest.raises(ValueError):
        model.predict_features(np.full(len(vector), np.nan))
