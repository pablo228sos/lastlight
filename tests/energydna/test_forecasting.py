"""Leakage, missing-target and actual trained-artifact regression tests."""

import numpy as np
import pandas as pd
import pytest

from research.energydna.data import make_windows, prepare, partition, window_features


def frames(hours=600):
    stamps = pd.date_range("2016-01-01", periods=hours, freq="h")
    meters = pd.DataFrame({"timestamp": stamps})
    for i, name in enumerate("abcdefghijkl"):
        meters[name] = 10 + i + np.sin(np.arange(hours) * 2 * np.pi / 24)
    meta = pd.DataFrame({"building_id": list("abcdefghijkl"), "timezone": ["UTC"] * 12})
    return meters, meta


def test_group_and_time_boundaries():
    meters, meta = frames()
    data, info = prepare(meters, meta)
    windows = make_windows(data, info)
    groups = info["building_groups"]
    assert not set(groups["train"]) & set(
        groups["validation"] + groups["generalization"]
    )
    assert not set(groups["validation"]) & set(groups["generalization"])
    for split, sample in partition(windows, info).items():
        assert len(sample["y"])
        for building, index in zip(sample["building"], sample["index"], strict=True):
            if split == "train":
                assert building in groups["train"] and index < info["train_end"]
            elif split == "validation":
                assert building not in groups["generalization"]
                assert info["train_end"] <= index < info["validation_end"]
            else:
                assert index >= info["validation_end"]


def test_future_changes_cannot_change_window_or_training():
    meters, meta = frames()
    data, info = prepare(meters, meta)
    original = partition(make_windows(data, info), info)["train"]
    meters.loc[info["train_end"] :, list("abcdefghijkl")] = 1_000_000
    changed, changed_info = prepare(meters, meta)
    altered = partition(make_windows(changed, changed_info), changed_info)["train"]
    for key in ["sequence", "static", "ridge", "scale", "y", "index"]:
        np.testing.assert_array_equal(original[key], altered[key])


def test_heldout_buildings_cannot_change_training_arrays():
    meters, meta = frames()
    data, info = prepare(meters, meta)
    original = partition(make_windows(data, info), info)["train"]
    heldout = (
        info["building_groups"]["validation"]
        + info["building_groups"]["generalization"]
    )
    meters[heldout] = 123456
    changed, info2 = prepare(meters, meta)
    altered = partition(make_windows(changed, info2), info2)["train"]
    for key in original:
        np.testing.assert_array_equal(original[key], altered[key])


def test_missing_inputs_are_causal_targets_never_imputed():
    values = np.arange(1, 169, dtype=float)
    values[1] = np.nan
    values[-2] = np.nan
    seq, _, _, scale = window_features(values, pd.Timestamp("2016-02-01"))
    assert seq[-2, 0] * scale == pytest.approx(166)
    assert seq[-2, 1] == 0
    assert np.isfinite(seq).all()
    meters, meta = frames()
    meters.loc[400, "a"] = np.nan
    data, info = prepare(meters, meta)
    windows = make_windows(data, info)
    assert not ((windows["building"] == "a") & (windows["index"] == 400)).any()
    # Missing weekly reference is excluded for every method on the common cohort.
    assert not ((windows["building"] == "a") & (windows["index"] == 568)).any()


def test_invalid_time_metadata_and_negative_values():
    meters, meta = frames()
    with pytest.raises(ValueError, match="metadata"):
        prepare(meters, meta.iloc[:-1])
    with pytest.raises(ValueError, match="hourly"):
        prepare(meters.drop(index=3), meta)
    meters.loc[400, "a"] = -1
    data, info = prepare(meters, meta)
    assert info["invalid_readings"] == 1
    assert np.isnan(data["a"].iloc[400])


def test_real_training_reload_and_tamper_rejection(tmp_path):
    from research.energydna.inference import EnergyPredictor
    from research.energydna.train import train

    meters, meta = frames()
    data, info = prepare(meters, meta)
    windows = make_windows(data, info)
    result = train(windows, info, tmp_path, max_epochs=2)
    assert result["training"]["epochs_run"] == 2
    assert result["training"]["weight_update_l1"] > 0
    second = train(windows, info, tmp_path / "repeat", max_epochs=2)
    assert result["weights_sha256"] == second["weights_sha256"]
    predictor = EnergyPredictor(tmp_path)
    assert b"\r\n" not in (tmp_path / "ridge.json").read_bytes()
    history = data["a"].to_numpy()[:168]
    value = predictor.predict(history, pd.Timestamp("2016-01-08"))
    assert np.isfinite(value) and value >= 0
    assert value == EnergyPredictor(tmp_path).predict(
        history, pd.Timestamp("2016-01-08")
    )
    with (tmp_path / "model.pt").open("ab") as handle:
        handle.write(b"corrupt")
    with pytest.raises(ValueError, match="checksum"):
        EnergyPredictor(tmp_path)


def test_committed_real_artifact_inference():
    from pathlib import Path
    from research.energydna.inference import EnergyPredictor

    artifact = (
        Path(__file__).resolve().parents[2] / "research/energydna/artifacts/gru-v1"
    )
    predictor = EnergyPredictor(artifact)
    assert b"\r\n" not in (artifact / "ridge.json").read_bytes()
    history = 25 + np.sin(np.arange(168) * np.pi / 12)
    for method in [
        "energydna_gru",
        "ridge",
        "seasonal_week",
        "seasonal_day",
        "persistence",
        "preferred",
    ]:
        value = predictor.predict(history, pd.Timestamp("2016-03-25 13:00"), method)
        assert np.isfinite(value) and value >= 0
    with pytest.raises(ValueError, match="168"):
        predictor.predict(history[:12], pd.Timestamp("2016-03-25 13:00"))
    with pytest.raises(ValueError, match="local"):
        predictor.predict(history, pd.Timestamp("2016-03-25 13:00Z"))
