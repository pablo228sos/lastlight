import numpy as np
from research.energydna.data import prepare
from research.energydna.multihour import HORIZON, windows
from test_forecasting import frames


def test_direct_horizon_has_no_future_inputs_or_overlapping_partitions():
    meters, meta = frames(600)
    data, info = prepare(meters, meta)
    sets = windows(data, info)
    assert HORIZON == 12
    for name, sample in sets.items():
        assert sample["y"].shape[1] == 12 and sample["sequence"].shape[1] == 168
        if name == "train":
            assert (sample["index"] + 12 <= info["train_end"]).all()
        if name == "validation":
            assert (
                (sample["index"] >= info["train_end"])
                & (sample["index"] + 12 <= info["validation_end"])
            ).all()
        if name in ["test", "generalization"]:
            assert (sample["index"] >= info["validation_end"]).all()
    before = sets["train"]
    meters.loc[info["train_end"] :, list("abcdefghijkl")] = 1_000_000
    changed, info2 = prepare(meters, meta)
    after = windows(changed, info2)["train"]
    for key in before:
        np.testing.assert_array_equal(before[key], after[key])


def test_committed_direct_horizon_artifact_loads_and_is_finite():
    import hashlib
    import json
    from pathlib import Path
    import torch
    from research.energydna import multihour

    root = Path(multihour.__file__).parent
    artifact = root / "artifacts/direct12-v1"
    report = json.loads((artifact / "evaluation.json").read_text())
    assert (
        hashlib.sha256((artifact / "model.pt").read_bytes()).hexdigest()
        == report["weights_sha256"]
    )
    assert (
        hashlib.sha256(
            Path(multihour.__file__).read_text(encoding="utf8").encode()
        ).hexdigest()
        == report["source_sha256"]
    )
    model = multihour.DirectGRU()
    model.load_state_dict(
        torch.load(artifact / "model.pt", map_location="cpu", weights_only=True)
    )
    meters, meta = frames(600)
    data, info = prepare(meters, meta)
    sample = multihour.windows(data, info)["test"]
    prediction = multihour.predict(model, sample)
    assert prediction.shape == sample["y"].shape
    assert np.isfinite(prediction).all() and (prediction >= 0).all()
