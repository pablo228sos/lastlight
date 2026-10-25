"""Separate direct 12-hour research model. Original one-hour artifact is intact."""

import copy
import hashlib
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import torch
from torch import nn

from research.energydna.data import load, window_features

HORIZON = 12


def windows(data, info):
    rows = []
    groups = info["building_groups"]
    for building in data:
        raw = data[building].to_numpy()
        for index in range(168, len(data) - HORIZON + 1, HORIZON):
            history = raw[index - 168 : index]
            target = raw[index : index + HORIZON]
            if (
                not np.isfinite(target).all()
                or not np.isfinite(history[:HORIZON]).all()
                or not np.isfinite(history[-24 : -24 + HORIZON]).all()
            ):
                continue
            try:
                _, static, ridge, scale = window_features(history, data.index[index])
            except ValueError:
                continue
            filled = pd.Series(history).ffill().fillna(0).to_numpy() / scale
            seq = np.column_stack((filled, np.isfinite(history))).astype(np.float32)
            day = history[-24 : -24 + HORIZON].copy() / scale
            split = None
            if building in groups["train"] and index + HORIZON <= info["train_end"]:
                split = "train"
            elif (
                building in groups["train"] + groups["validation"]
                and index >= info["train_end"]
                and index + HORIZON <= info["validation_end"]
            ):
                split = "validation"
            elif building in groups["train"] and index >= info["validation_end"]:
                split = "test"
            elif (
                building in groups["generalization"] and index >= info["validation_end"]
            ):
                split = "generalization"
            if split:
                rows.append(
                    (
                        split,
                        seq,
                        static,
                        ridge,
                        scale,
                        target.copy(),
                        building,
                        index,
                        day,
                        history[:HORIZON].copy() / scale,
                        history[-1] / scale,
                    )
                )
    result = {}
    names = [
        "sequence",
        "static",
        "ridge",
        "scale",
        "y",
        "building",
        "index",
        "day",
        "week",
        "last",
    ]
    for split in ["train", "validation", "test", "generalization"]:
        selected = [row[1:] for row in rows if row[0] == split]
        if not selected:
            raise ValueError("Every direct-horizon cohort must be nonempty")
        result[split] = {
            name: np.asarray([r[i] for r in selected]) for i, name in enumerate(names)
        }
    return result


class DirectGRU(nn.Module):
    def __init__(self):
        super().__init__()
        self.gru = nn.GRU(2, 16, batch_first=True)
        self.head = nn.Sequential(nn.Linear(36, 32), nn.ReLU(), nn.Linear(32, HORIZON))
        nn.init.zeros_(self.head[-1].weight)
        nn.init.zeros_(self.head[-1].bias)

    def forward(self, sequence, static, day):
        _, hidden = self.gru(sequence)
        return (day + self.head(torch.cat((hidden[-1], static, day), dim=1))).clamp_min(
            0
        )


def predict(model, sample):
    model.eval()
    with torch.inference_mode():
        return (
            model(
                torch.tensor(sample["sequence"], dtype=torch.float32),
                torch.tensor(sample["static"], dtype=torch.float32),
                torch.tensor(sample["day"], dtype=torch.float32),
            )
            .numpy()
            .astype(float)
            * sample["scale"][:, None]
        )


def scores(sample, predictions, info):
    error = sample["y"] - predictions
    per_building = {}
    for building in sorted(set(sample["building"])):
        mask = sample["building"] == building
        e = error[mask]
        per_building[str(building)] = {
            "origins": int(mask.sum()),
            "mae_kw": float(np.abs(e).mean()),
            "rmse_kw": float(np.sqrt(np.mean(e**2))),
            "history_scaled_mae": float(
                np.mean(np.abs(e) / sample["scale"][mask, None])
            ),
            "degenerate_training_prefix": info["per_building"][str(building)][
                "training_prefix_constant"
            ],
        }
    active = [v for v in per_building.values() if not v["degenerate_training_prefix"]]
    return {
        "origins": len(error),
        "target_hours": int(error.size),
        "mae_kw": float(np.abs(error).mean()),
        "rmse_kw": float(np.sqrt(np.mean(error**2))),
        "macro_history_scaled_mae": float(
            np.mean([v["history_scaled_mae"] for v in per_building.values()])
        ),
        "nonconstant_macro_mae_kw": float(np.mean([v["mae_kw"] for v in active]))
        if active
        else None,
        "per_horizon_hour": [
            {
                "hour": i + 1,
                "mae_kw": float(np.abs(error[:, i]).mean()),
                "rmse_kw": float(np.sqrt(np.mean(error[:, i] ** 2))),
            }
            for i in range(HORIZON)
        ],
        "per_building": per_building,
    }


def train(data, info, output, max_epochs=80):
    started = perf_counter()
    torch.manual_seed(20261026)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    sets = windows(data, info)
    tr, va = sets["train"], sets["validation"]
    scaler = StandardScaler().fit(tr["ridge"])
    ridge = Ridge(alpha=10.0).fit(
        scaler.transform(tr["ridge"]), tr["y"] / tr["scale"][:, None]
    )
    model = DirectGRU()
    initial = copy.deepcopy(model.state_dict())
    opt = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.001)
    seq = torch.tensor(tr["sequence"], dtype=torch.float32)
    st = torch.tensor(tr["static"], dtype=torch.float32)
    dy = torch.tensor(tr["day"], dtype=torch.float32)
    y = torch.tensor(tr["y"] / tr["scale"][:, None], dtype=torch.float32)
    best, state, stale = float("inf"), None, 0
    history = []
    for epoch in range(max_epochs):
        model.train()
        for batch in torch.randperm(len(y)).split(64):
            opt.zero_grad()
            loss = nn.functional.smooth_l1_loss(
                model(seq[batch], st[batch], dy[batch]), y[batch]
            )
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        score = scores(va, predict(model, va), info)["macro_history_scaled_mae"]
        history.append(score)
        if score < best - 1e-7:
            best, state, stale = score, copy.deepcopy(model.state_dict()), 0
        else:
            stale += 1
        if stale >= 10:
            break
    model.load_state_dict(state)
    model.eval()
    output.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output / "model.pt")

    def predictions(s):
        return {
            "persistence": np.repeat(s["last"][:, None], HORIZON, axis=1)
            * s["scale"][:, None],
            "seasonal_day": s["day"] * s["scale"][:, None],
            "seasonal_week": s["week"] * s["scale"][:, None],
            "ridge": np.maximum(0, ridge.predict(scaler.transform(s["ridge"])))
            * s["scale"][:, None],
            "direct_gru": predict(model, s),
        }

    validation = {
        name: scores(va, p, info)["macro_history_scaled_mae"]
        for name, p in predictions(va).items()
    }
    preferred = min(validation, key=validation.get)
    baseline = {
        "mean": scaler.mean_.tolist(),
        "scale": scaler.scale_.tolist(),
        "coef": ridge.coef_.tolist(),
        "intercept": ridge.intercept_.tolist(),
        "alpha": 10.0,
        "fit": "train only",
    }
    (output / "ridge.json").write_text(
        json.dumps(baseline, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    digest = hashlib.sha256((output / "model.pt").read_bytes()).hexdigest()
    report = {
        "model_version": "energydna-direct12-v1-" + digest[:12],
        "weights_sha256": digest,
        "source_sha256": hashlib.sha256(
            Path(__file__).read_text(encoding="utf8").encode()
        ).hexdigest(),
        "horizon_hours": HORIZON,
        "history_hours": 168,
        "origin_stride_hours": 12,
        "method": "direct complete-horizon prediction; no observed future load in any input",
        "data_preparation_metadata": info,
        "training": {
            "seed": 20261026,
            "max_epochs": max_epochs,
            "epochs_run": len(history),
            "best_epoch": int(np.argmin(history)) + 1,
            "validation_history": history,
            "weight_update_l1": float(
                sum((model.state_dict()[k] - initial[k]).abs().sum() for k in initial)
            ),
            "architecture": "168h load+mask -> GRU16 + static8 + past-day12 -> head36/32/12",
            "optimizer": "AdamW .001 decay .001 batch64 SmoothL1 clip1 patience10",
            "parameter_count": sum(p.numel() for p in model.parameters()),
        },
        "validation_selection": validation,
        "preferred_method": preferred,
        "metrics": {
            name: {method: scores(s, p, info) for method, p in predictions(s).items()}
            for name, s in sets.items()
            if name != "train"
        },
        "elapsed_seconds": perf_counter() - started,
        "original_one_hour_model_preserved": True,
        "deployed_in_application": False,
        "not_critical_load_or_kyrgyz_measurements": True,
    }
    reloaded = DirectGRU()
    reloaded.load_state_dict(
        torch.load(output / "model.pt", map_location="cpu", weights_only=True)
    )
    np.testing.assert_array_equal(
        predict(model, sets["test"]), predict(reloaded, sets["test"])
    )
    report["saved_artifact_replay_exact"] = True
    (output / "evaluation.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    print(
        json.dumps(
            {
                "model": report["model_version"],
                "epochs": len(history),
                "preferred": preferred,
                "test": {
                    m: {
                        k: v[k]
                        for k in ["mae_kw", "rmse_kw", "origins", "target_hours"]
                    }
                    for m, v in report["metrics"]["test"].items()
                },
            }
        ),
        flush=True,
    )
    return report


def main():
    data, info = load(Path("research/energydna/data"))
    # Descriptive audit only. No target deletion based on these full-period summaries.
    quality = {
        b: {
            "usage": b.split("_")[1],
            "observed": int(data[b].notna().sum()),
            "zero_count": int((data[b] == 0).sum()),
            "missing_fraction": float(data[b].isna().mean()),
            "mean_kw": float(data[b].mean()) if data[b].notna().any() else None,
            "p99_kw": float(data[b].quantile(0.99)) if data[b].notna().any() else None,
            "largest_one_hour_change_kw": float(data[b].diff().abs().max())
            if data[b].notna().any()
            else None,
        }
        for b in data
    }
    output = Path("research/energydna/artifacts/direct12-v1")
    output.mkdir(parents=True, exist_ok=True)
    (output / "cohort-quality.json").write_text(
        json.dumps(quality, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    train(data, info, output)


if __name__ == "__main__":
    main()
