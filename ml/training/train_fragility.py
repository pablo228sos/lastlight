"""Train on train only; select weights, calibration and thresholds on validation."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
from time import perf_counter

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from sklearn.linear_model import LogisticRegression
import torch
from torch import nn

from ml.data.generate_scenarios import distribution
from ml.evaluation.metrics import choose_threshold, metrics
from ml.features import FEATURE_NAMES, FEATURE_VERSION
from ml.models.fragility_net import FragilityNet, FragilityPredictor
from services.simulation import MODEL_VERSION


def temperature(logits, labels):
    def objective(log_t):
        z = logits / np.exp(log_t)
        return float(np.mean(np.logaddexp(0, z) - labels * z))

    return float(np.exp(minimize_scalar(objective, bounds=(-2, 2), method="bounded").x))


def train(data: pd.DataFrame, output: Path, seed=20261024, max_epochs=240) -> dict:
    started = perf_counter()
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    if set(data.physics_version) != {MODEL_VERSION} or set(data.feature_version) != {FEATURE_VERSION}:
        raise ValueError('Dataset physics/preprocessing versions do not match this implementation')
    if not data.scenario_id.is_unique or not data.input_hash.is_unique:
        raise ValueError('Scenario identities and input hashes must be unique')
    all_features = np.stack(data.features)
    if all_features.shape[1] != len(FEATURE_NAMES) or not np.isfinite(all_features).all():
        raise ValueError('Dataset features have an invalid shape or nonfinite values')
    # Prevent train/test contamination even when callers supply a custom parquet.
    if data.physical_signature.duplicated().any():
        raise ValueError("Duplicate physical scenarios are forbidden")
    sets = {name: rows for name, rows in data.groupby("split")}
    if not {"train", "validation", "test", "generalization"} <= set(sets):
        raise ValueError("All four independent splits are required")
    for left in sets:
        for right in sets:
            if left != right and set(sets[left].equipment_id) & set(
                sets[right].equipment_id
            ):
                raise ValueError("Equipment configuration leakage across splits")
    train_x = np.stack(sets["train"].features)
    mean, scale = train_x.mean(axis=0), train_x.std(axis=0)
    scale[scale < 1e-9] = 1
    arrays = {
        name: (
            (np.stack(rows.features) - mean) / scale,
            rows.failed.to_numpy(dtype=np.float32),
        )
        for name, rows in sets.items()
    }
    x, y = arrays["train"]
    vx, vy = arrays["validation"]
    if len(np.unique(y)) != 2 or len(np.unique(vy)) != 2:
        raise ValueError("Train and validation each require both outcome classes")
    baseline = LogisticRegression(
        max_iter=2000, class_weight="balanced", random_state=seed
    ).fit(x, y)
    network = FragilityNet()
    optimizer = torch.optim.AdamW(network.parameters(), lr=0.002, weight_decay=0.001)
    criterion = nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor(float((y == 0).sum() / max(1, (y == 1).sum())))
    )
    tx, ty = torch.tensor(x, dtype=torch.float32), torch.tensor(y)
    valx = torch.tensor(vx, dtype=torch.float32)
    best_loss, best_state, stale = float("inf"), None, 0
    history = []
    for epoch in range(max_epochs):
        network.train()
        order = torch.randperm(len(tx))
        for batch in order.split(256):
            optimizer.zero_grad()
            loss = criterion(network(tx[batch]), ty[batch])
            loss.backward()
            optimizer.step()
        network.eval()
        with torch.inference_mode():
            val_loss = float(
                nn.functional.binary_cross_entropy_with_logits(
                    network(valx), torch.tensor(vy)
                )
            )
        history.append(val_loss)
        if val_loss < best_loss - 1e-5:
            best_loss, best_state, stale = (
                val_loss,
                copy.deepcopy(network.state_dict()),
                0,
            )
        else:
            stale += 1
        if stale >= 20:
            break
    network.load_state_dict(best_state)
    network.eval()
    with torch.inference_mode():
        logits = network(valx).numpy()
    base_logits = baseline.decision_function(vx)
    temp, base_temp = temperature(logits, vy), temperature(base_logits, vy)

    def score(z, t):
        return 1 / (1 + np.exp(-np.clip(z / t, -40, 40)))

    threshold = choose_threshold(vy, score(logits, temp))
    base_threshold = choose_threshold(vy, score(base_logits, base_temp))
    data_report = distribution(data)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    torch.save(network.state_dict(), output / "model.pt")
    checkpoint_hash = hashlib.sha256((output / "model.pt").read_bytes()).hexdigest()
    meta = {
        "model_version": f"fragility-1-{checkpoint_hash[:12]}",
        "feature_version": FEATURE_VERSION,
        "feature_names": FEATURE_NAMES,
        "physics_version": MODEL_VERSION,
        "seed": seed,
        "mean": mean.tolist(),
        "scale": scale.tolist(),
        "domain_min": train_x.min(axis=0).tolist(),
        "domain_max": train_x.max(axis=0).tolist(),
        "temperature": temp,
        "threshold": threshold,
        "baseline_temperature": base_temp,
        "baseline_threshold": base_threshold,
        "baseline_coefficients": baseline.coef_[0].tolist(),
        "baseline_intercept": float(baseline.intercept_[0]),
        "checkpoint_sha256": checkpoint_hash,
        "dataset_hash": data_report["dataset_hash"],
        "training_rows": len(x),
        "epochs": len(history),
        "best_validation_loss": best_loss,
        "normalization_fitted_on": "train only",
        "torch_version": str(torch.__version__),
        "provenance": "synthetic_simulation; not measured failures",
    }
    (output / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf8")
    predictor = FragilityPredictor.load(output)
    report = {
        "model_version": meta["model_version"],
        "dataset": data_report,
        "seed": seed,
        "epochs": len(history),
        "training_seconds": perf_counter() - started,
        "selection": "early stopping, temperature and F2 threshold fitted only on validation",
        "limitations": [
            "Synthetic labels only; no real-world outage probabilities.",
            "Summary features discard temporal ordering; every engineering result requires physics.",
        ],
    }
    for split in ["validation", "test", "generalization"]:
        raw = np.stack(sets[split].features)
        labels = sets[split].failed.to_numpy()
        scores = predictor.scores(raw)
        report[split] = {
            "baseline": metrics(
                labels, predictor.scores(raw, baseline=True), base_threshold
            ),
            "fragility_net": metrics(labels, scores, threshold),
        }
        if split != "validation":
            missed = sets[split][labels & (scores < threshold)]
            report[split]["false_negative_examples"] = (
                missed[
                    [
                        "scenario_id",
                        "equipment_id",
                        "parameters_json",
                        "first_failure_hours",
                        "unserved_critical_kwh",
                    ]
                ]
                .head(12)
                .to_dict(orient="records")
            )
    report["outperforms_baseline_test_f1"] = (
        report["test"]["fragility_net"]["f1"] > report["test"]["baseline"]["f1"]
    )
    (output / "evaluation.json").write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf8"
    )
    print(
        json.dumps(
            {
                k: report[k]
                for k in [
                    "model_version",
                    "epochs",
                    "training_seconds",
                    "test",
                    "generalization",
                ]
            },
            indent=2,
        )
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data", type=Path, default=Path("ml/data/generated/scenarios.parquet")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("ml/artifacts/fragility-v1")
    )
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--epochs", type=int, default=240)
    args = parser.parse_args()
    train(pd.read_parquet(args.data), args.output, args.seed, args.epochs)


if __name__ == "__main__":
    main()
