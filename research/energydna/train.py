"""Actual deterministic CPU GRU training; model selection uses validation only."""

import argparse
import copy
from importlib.metadata import version
import json
from pathlib import Path
import platform
import random
from time import perf_counter

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import torch

from research.energydna.data import (
    FEATURE_VERSION,
    load,
    make_windows,
    partition,
    source_hash,
)
from research.energydna.download import sha256
from research.energydna.model import EnergyDNA


def predict_network(model, sample):
    model.eval()
    outputs = []
    with torch.inference_mode():
        for start in range(0, len(sample["y"]), 512):
            seq = torch.tensor(
                sample["sequence"][start : start + 512], dtype=torch.float32
            )
            static = torch.tensor(
                sample["static"][start : start + 512], dtype=torch.float32
            )
            outputs.append(model(seq, static).numpy())
    return np.concatenate(outputs).astype(float) * sample["scale"]


def metrics(sample, predictions, info):
    if not len(sample["y"]):
        return {"n": 0}
    error = sample["y"] - predictions
    per_building = {}
    for building in sorted(set(sample["building"])):
        mask = sample["building"] == building
        e = error[mask]
        per_building[str(building)] = {
            "n": int(mask.sum()),
            "mae_kw": float(np.abs(e).mean()),
            "rmse_kw": float(np.sqrt(np.mean(e**2))),
            "history_scaled_mae": float((np.abs(e) / sample["scale"][mask]).mean()),
            "training_prefix_constant": info["per_building"][str(building)][
                "training_prefix_constant"
            ],
        }
    active = [m for m in per_building.values() if not m["training_prefix_constant"]]
    return {
        "n": len(error),
        "mae_kw": float(np.abs(error).mean()),
        "rmse_kw": float(np.sqrt(np.mean(error**2))),
        "macro_history_scaled_mae": float(
            np.mean([m["history_scaled_mae"] for m in per_building.values()])
        ),
        "nonconstant_macro_mae_kw": float(np.mean([m["mae_kw"] for m in active]))
        if active
        else None,
        "per_building": per_building,
    }


def all_predictions(model, baseline, sample):
    ridge_x = (sample["ridge"] - np.array(baseline["mean"])) / np.array(
        baseline["scale"]
    )
    return {
        "seasonal_week": sample["static"][:, 2].astype(float) * sample["scale"],
        "seasonal_day": sample["static"][:, 1].astype(float) * sample["scale"],
        "persistence": sample["static"][:, 0].astype(float) * sample["scale"],
        "ridge": np.maximum(
            0, ridge_x @ np.array(baseline["coef"]) + baseline["intercept"]
        )
        * sample["scale"],
        "energydna_gru": predict_network(model, sample),
    }


def benchmark(model, baseline, splits, info):
    return {
        split: {
            name: metrics(sample, pred, info)
            for name, pred in all_predictions(model, baseline, sample).items()
        }
        for split, sample in splits.items()
        if split != "train"
    }


def train(
    windows: dict, info: dict, output: Path, seed=20261024, max_epochs=100
) -> dict:
    if not 1 <= max_epochs <= 500:
        raise ValueError("Use 1..500 bounded training epochs")
    started = perf_counter()
    frozen_source = source_hash()
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    splits = partition(windows, info)
    train_set, val_set = splits["train"], splits["validation"]
    scaler = StandardScaler().fit(train_set["ridge"])
    ridge = Ridge(alpha=10.0).fit(
        scaler.transform(train_set["ridge"]), train_set["y"] / train_set["scale"]
    )
    baseline = {
        "method": "ridge",
        "alpha": 10.0,
        "mean": scaler.mean_.tolist(),
        "scale": scaler.scale_.tolist(),
        "coef": ridge.coef_.tolist(),
        "intercept": float(ridge.intercept_),
        "fit_partition": "train only",
    }
    model = EnergyDNA()
    initial = copy.deepcopy(model.state_dict())
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.001)
    sequence = torch.tensor(train_set["sequence"], dtype=torch.float32)
    static = torch.tensor(train_set["static"], dtype=torch.float32)
    target = torch.tensor(train_set["y"] / train_set["scale"], dtype=torch.float32)
    best_score, best_state, stale, best_epoch = float("inf"), None, 0, 0
    history = []
    for epoch in range(max_epochs):
        model.train()
        loss_sum = 0.0
        order = torch.randperm(len(target))
        for batch in order.split(128):
            optimizer.zero_grad()
            prediction = model(sequence[batch], static[batch])
            loss = torch.nn.functional.smooth_l1_loss(prediction, target[batch])
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            loss_sum += float(loss.detach()) * len(batch)
        val_prediction = predict_network(model, val_set)
        score = metrics(val_set, val_prediction, info)["macro_history_scaled_mae"]
        history.append(
            {
                "epoch": epoch + 1,
                "train_smooth_l1": loss_sum / len(target),
                "validation_macro_history_scaled_mae": score,
            }
        )
        if score < best_score - 1e-7:
            best_score, best_state, best_epoch, stale = (
                score,
                copy.deepcopy(model.state_dict()),
                epoch + 1,
                0,
            )
        else:
            stale += 1
        if (epoch + 1) % 10 == 0:
            print(
                f"epoch={epoch + 1} validation={score:.6f} best={best_score:.6f}",
                flush=True,
            )
        if stale >= 12:
            break
    model.load_state_dict(best_state)
    validation = {
        name: metrics(val_set, prediction, info)["macro_history_scaled_mae"]
        for name, prediction in all_predictions(model, baseline, val_set).items()
    }
    preferred = min(validation, key=validation.get)
    output.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output / "model.pt")
    (output / "ridge.json").write_text(
        json.dumps(baseline, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    identity = sha256(output / "model.pt")
    training = {
        "seed": seed,
        "max_epochs": max_epochs,
        "epochs_run": len(history),
        "best_epoch": best_epoch,
        "optimizer": "AdamW",
        "learning_rate": 0.001,
        "weight_decay": 0.001,
        "batch_size": 128,
        "patience": 12,
        "loss": "SmoothL1 on per-origin history-scaled targets",
        "selection": "minimum validation macro-building history-scaled MAE; no test selection",
        "weight_update_l1": float(
            sum((model.state_dict()[key] - initial[key]).abs().sum() for key in initial)
        ),
        "history": history,
    }
    if source_hash() != frozen_source:
        raise ValueError(
            "Research source changed during training; rerun on frozen code"
        )
    manifest = {
        "model_version": "energydna-gru-v1-" + identity[:12],
        "feature_version": FEATURE_VERSION,
        "source_sha256": frozen_source,
        "weights_sha256": identity,
        "ridge_sha256": sha256(output / "ridge.json"),
        "architecture": {
            "type": "GRU seasonal residual",
            "input_channels": ["past load / observed-window mean", "observed mask"],
            "sequence_hours": 48,
            "hidden_size": 16,
            "layers": 1,
            "static_features": [
                "lag1 / scale",
                "lag24 / scale",
                "lag168 / scale",
                "missing_fraction_168",
                "target_hour_sin",
                "target_hour_cos",
                "target_dow_sin",
                "target_dow_cos",
            ],
            "head": [24, 16, 1],
            "parameter_count": sum(p.numel() for p in model.parameters()),
        },
        "horizon_hours": 1,
        "lookback_hours": 168,
        "units": info["units"],
        "data": info,
        "training": training,
        "preferred_method": preferred,
        "validation_selection_scores": validation,
        "environment": {
            "python": platform.python_version(),
            **{
                name: version(name)
                for name in ["numpy", "pandas", "torch", "scikit-learn"]
            },
        },
        "boundaries": [
            "Historical overseas whole-building research only",
            "No critical-circuit equivalence or geographic transfer validation",
            "No physical trace injection, weather inputs, or API integration",
            "Preferred method selected on validation; test is independent evidence, not tuning",
        ],
        "derived_artifact_license": "CC BY-SA 4.0; upstream attribution and license link in data.source and NOTICE.md",
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    report = {
        "model_version": manifest["model_version"],
        "weights_sha256": identity,
        "source_sha256": manifest["source_sha256"],
        "preferred_method": preferred,
        "selection_split": "validation",
        "training": training,
        "metrics": benchmark(model, baseline, splits, info),
        "elapsed_seconds": perf_counter() - started,
    }
    (output / "evaluation.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    print(
        json.dumps(
            {
                "model_version": manifest["model_version"],
                "preferred_method": preferred,
                "validation": validation,
                "epochs": len(history),
                "seconds": report["elapsed_seconds"],
            }
        ),
        flush=True,
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("research/energydna/data"))
    parser.add_argument(
        "--output", type=Path, default=Path("research/energydna/artifacts/gru-v1")
    )
    parser.add_argument("--max-epochs", type=int, default=100)
    args = parser.parse_args()
    data, info = load(args.data)
    train(make_windows(data, info), info, args.output, max_epochs=args.max_epochs)


if __name__ == "__main__":
    main()
