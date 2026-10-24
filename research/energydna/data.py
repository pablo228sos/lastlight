"""Causal rolling-origin windows, common baseline cohort and disjoint groups."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.energydna.download import sha256

FEATURE_VERSION = "energydna-hourly-1"
LOOKBACK = 168
SEQUENCE_HOURS = 48
HORIZON_HOURS = 1
MIN_OBSERVED = 0.8


def source_hash() -> str:
    """Canonical source fingerprint, independent of checkout newline style."""
    root = Path(__file__).parent
    content = "\n".join(
        (root / name).read_text(encoding="utf8")
        for name in [
            "data.py",
            "model.py",
            "train.py",
            "inference.py",
            "evaluate.py",
        ]
    )
    return hashlib.sha256(content.encode()).hexdigest()


def load(data_dir: Path):
    manifest = json.loads((data_dir / "source.json").read_text(encoding="utf8"))
    for name, expected in manifest["sha256"].items():
        if sha256(data_dir / name) != expected:
            raise ValueError(f"Source checksum mismatch: {name}")
    data, info = prepare(
        pd.read_csv(data_dir / "electricity.csv"),
        pd.read_csv(data_dir / "metadata.csv"),
    )
    info["source"] = manifest
    return data, info


def prepare(meters: pd.DataFrame, metadata: pd.DataFrame):
    if "timestamp" not in meters or len(meters) < 480:
        raise ValueError("At least 480 strictly hourly rows required")
    stamps = pd.DatetimeIndex(pd.to_datetime(meters.timestamp, errors="raise"))
    if (
        stamps.tz is not None
        or stamps.hasnans
        or not stamps.equals(pd.date_range(stamps[0], periods=len(stamps), freq="h"))
    ):
        raise ValueError(
            "Unique contiguous naive source-local hourly timestamps required"
        )
    names = sorted(set(meters.columns) - {"timestamp"})
    if (
        not {"building_id", "timezone"} <= set(metadata.columns)
        or metadata.building_id.duplicated().any()
        or not set(names) <= set(metadata.building_id)
    ):
        raise ValueError("Unique matching building metadata required")
    if len(names) < 6:
        raise ValueError("At least six building groups required")
    values = meters[names].apply(pd.to_numeric, errors="coerce").astype(float)
    invalid = ((values < 0) | ~np.isfinite(values)) & values.notna()
    values = values.mask(invalid)
    values.index = stamps
    ordered = np.random.default_rng(20261024).permutation(names).tolist()
    ntrain, nval = max(1, int(len(names) * 0.6)), max(1, int(len(names) * 0.2))
    groups = {
        "train": ordered[:ntrain],
        "validation": ordered[ntrain : ntrain + nval],
        "generalization": ordered[ntrain + nval :],
    }
    train_end, val_end = int(len(stamps) * 0.6), int(len(stamps) * 0.8)
    info = {
        "feature_version": FEATURE_VERSION,
        "horizon_hours": HORIZON_HOURS,
        "lookback_hours": LOOKBACK,
        "sequence_hours": SEQUENCE_HOURS,
        "hours": len(stamps),
        "building_groups": groups,
        "train_end": train_end,
        "validation_end": val_end,
        "periods": {
            "start": str(stamps[0]),
            "validation_start": str(stamps[train_end]),
            "test_start": str(stamps[val_end]),
            "end_inclusive": str(stamps[-1]),
        },
        "missing_readings": int(values.isna().sum().sum()),
        "invalid_readings": int(invalid.sum().sum()),
        "per_building": {
            name: {
                "missing": int(values[name].isna().sum()),
                "zero_readings": int((values[name] == 0).sum()),
                "training_prefix_observed": int(
                    values[name].iloc[:train_end].notna().sum()
                ),
                "training_prefix_constant": bool(
                    values[name].iloc[:train_end].dropna().nunique() <= 1
                ),
            }
            for name in names
        },
        "units": "whole-building hourly average kW (hourly kWh / 1 h)",
        "timestamp_policy": "source-local naive clock; no timezone conversion or DST/weather join",
        "missing_policy": "No target imputation. Require observed target/lags 1,24,168 and >=80% observed preceding 168h. Forward-fill inputs inside past window only, leading gaps zero; provide missing mask. Zeros retained; no full-series anomaly filter.",
        "evaluation_protocol": "one-hour rolling origin; earlier observed test hours may enter later windows; no parameter refitting on validation/test buildings or periods",
    }
    return values, info


def calendar(target: pd.Timestamp) -> np.ndarray:
    return np.array(
        [
            np.sin(2 * np.pi * target.hour / 24),
            np.cos(2 * np.pi * target.hour / 24),
            np.sin(2 * np.pi * target.day_of_week / 7),
            np.cos(2 * np.pi * target.day_of_week / 7),
        ],
        dtype=np.float32,
    )


def window_features(history, target: pd.Timestamp):
    history = np.asarray(history, dtype=float)
    if (
        history.shape != (LOOKBACK,)
        or np.isinf(history).any()
        or (history[np.isfinite(history)] < 0).any()
    ):
        raise ValueError("Exactly 168 hourly nonnegative readings or NaN required")
    observed = np.isfinite(history)
    if observed.mean() < MIN_OBSERVED or not observed[[-1, -24, -168]].all():
        raise ValueError("Insufficient observed causal history or baseline lags")
    scale = max(1.0, float(history[observed].mean()))
    filled = pd.Series(history).ffill().fillna(0).to_numpy() / scale
    sequence = np.column_stack(
        (filled[-SEQUENCE_HOURS:], observed[-SEQUENCE_HOURS:])
    ).astype(np.float32)
    static = np.r_[
        filled[-1], filled[-24], filled[-168], 1 - observed.mean(), calendar(target)
    ].astype(np.float32)
    ridge = np.r_[filled[-24:], observed[-24:], static].astype(np.float32)
    return sequence, static, ridge, scale


def make_windows(data: pd.DataFrame, info: dict) -> dict:
    rows = {
        name: []
        for name in [
            "sequence",
            "static",
            "ridge",
            "scale",
            "y",
            "building",
            "index",
            "timestamp",
        ]
    }
    skipped = {}
    for building in data:
        values = data[building].to_numpy()
        skipped[building] = 0
        for index in range(LOOKBACK, len(data)):
            if not np.isfinite(values[index]):
                skipped[building] += 1
                continue
            try:
                seq, static, ridge, scale = window_features(
                    values[index - LOOKBACK : index], data.index[index]
                )
            except ValueError:
                skipped[building] += 1
                continue
            for key, value in zip(
                rows,
                [
                    seq,
                    static,
                    ridge,
                    scale,
                    values[index],
                    building,
                    index,
                    str(data.index[index]),
                ],
                strict=True,
            ):
                rows[key].append(value)
    info["excluded_windows"] = skipped
    if not rows["y"]:
        raise ValueError("No eligible observed windows")
    return {name: np.asarray(values) for name, values in rows.items()}


def partition(windows: dict, info: dict) -> dict:
    groups, index, building = (
        info["building_groups"],
        windows["index"],
        windows["building"],
    )
    train = np.isin(building, groups["train"])
    validation = np.isin(building, groups["validation"])
    generalization = np.isin(building, groups["generalization"])
    masks = {
        "train": train & (index < info["train_end"]),
        "validation": (train | validation)
        & (index >= info["train_end"])
        & (index < info["validation_end"]),
        "test": train & (index >= info["validation_end"]),
        "generalization": generalization & (index >= info["validation_end"]),
    }
    result = {
        split: {name: values[mask] for name, values in windows.items()}
        for split, mask in masks.items()
    }
    if any(not len(group["y"]) for group in result.values()):
        raise ValueError(
            "Every train/validation/test/generalization cohort must be nonempty"
        )
    return result
