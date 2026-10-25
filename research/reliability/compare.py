"""One preregistered comparison; old test is diagnostic, fresh holdout is final."""

import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
import torch
from torch import nn

from ml_bridge.features import features
from ml_bridge.inference import FragilityPredictor
from ml_bridge.metrics import choose_threshold, metrics
from ml_bridge.runtime import source_identity
from ml_bridge.train import temperature
from research.reliability.features import NAMES, timing_features
from services.simulation.engine import simulate
from services.simulation.schemas import SimulationRequest

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "research/reliability/artifacts"


def safety_threshold(y, score):
    eligible = []
    for threshold in np.linspace(0.01, 0.99, 99):
        result = metrics(y, score, threshold)
        if result["dangerous_recall"] >= 0.99 and result["precision"] >= 0.80:
            eligible.append((result["precision"], threshold))
    return (
        (float(max(eligible)[1]), True)
        if eligible
        else (choose_threshold(y, score), False)
    )


def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -40, 40)))


def error_audit(old, frozen):
    subset = old[old.split == "test"]
    score = frozen.scores(np.stack(subset.features))
    missed = subset[subset.failed & (score < frozen.manifest["threshold"])]
    cases = []
    for row in missed.itertuples():
        s = SimulationRequest.model_validate_json(row.parameters_json)
        physical = simulate(s)
        index = next(
            i
            for i, point in enumerate(physical.trace)
            if point.unserved_critical_kw > 1e-9
        )
        point = physical.trace[index]
        online = (
            s.grid.profile_online
            if s.grid.profile_online is not None
            else [s.grid.online] * s.interval_count
        )
        transitions = [
            i * s.step_minutes / 60
            for i in range(1, len(online))
            if online[i] and not online[i - 1]
        ]
        raw = np.array(features(s))
        flags = {
            "battery_at_minimum": point.battery_soc <= s.battery.minimum_soc + 1e-9,
            "inverter_smaller_than_critical": not point.grid_online
            and s.inverter.max_kw < s.load.critical_kw,
            "discharge_limit_smaller_than_critical": s.battery.max_discharge_kw
            < s.load.critical_kw,
            "grid_forming_unavailable": not point.grid_online
            and not s.inverter.islanding_capable,
            "pv_present_but_islanding_blocked": not point.grid_online
            and point.solar_available_kw > 0
            and not (s.inverter.islanding_capable and s.solar.islanding_capable),
            "solar_absent_at_failure": point.solar_available_kw <= 1e-9,
            "grid_offline_at_failure": not point.grid_online,
            "noncritical_not_shed": not s.load.shed_noncritical_during_outage
            and s.load.noncritical_kw > 0,
            "outside_old_training_feature_range": bool(
                (
                    (raw < frozen.manifest["domain_min"])
                    | (raw > frozen.manifest["domain_max"])
                ).any()
            ),
            "failure_within_one_step_of_horizon": s.duration_hours - point.elapsed_hours
            <= s.step_minutes / 60 + 1e-9,
        }
        cases.append(
            {
                "scenario_id": row.scenario_id,
                "input_hash": row.input_hash,
                "equipment_id": row.equipment_id,
                "physical_summary": physical.summary.model_dump(mode="json"),
                "trace_before_and_at_failure": [
                    p.model_dump(mode="json")
                    for p in physical.trace[max(0, index - 1) : index + 2]
                ],
                "flags": flags,
                "grid_restoration_hours": transitions,
                "critical_kw": s.load.critical_kw,
                "inverter_kw": s.inverter.max_kw,
                "maximum_discharge_kw": s.battery.max_discharge_kw,
                "discharge_efficiency": s.battery.discharge_efficiency,
                "input": s.model_dump(mode="json"),
            }
        )
    assert len(cases) == 20
    return {
        "n": 20,
        "interpretation": "Overlapping trace-supported diagnostic flags, not exclusive causal attributions; no fitting or threshold selection on these cases.",
        "flag_counts": {
            name: sum(c["flags"][name] for c in cases) for name in cases[0]["flags"]
        },
        "cases": cases,
    }


def main():
    torch.manual_seed(20261025)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    old = pd.read_parquet(ROOT / "ml_bridge/data/generated/scenarios.parquet")
    frozen = FragilityPredictor.load(ROOT / "ml_bridge/artifacts/fragility-official-v1")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    audit = error_audit(old, frozen)
    (OUTPUT / "original-false-negatives.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    train, val = old[old.split == "train"], old[old.split == "validation"]

    def parse(rows):
        return [SimulationRequest.model_validate_json(v) for v in rows.parameters_json]

    tx, vx = (
        np.stack([timing_features(s) for s in parse(train)]),
        np.stack([timing_features(s) for s in parse(val)]),
    )
    mean, scale = tx.mean(0), tx.std(0)
    scale[scale < 1e-9] = 1
    x, v = (tx - mean) / scale, (vx - mean) / scale
    y, vy = (
        train.failed.to_numpy(dtype=np.float32),
        val.failed.to_numpy(dtype=np.float32),
    )
    logistic = LogisticRegression(
        max_iter=2000, class_weight="balanced", random_state=20261025
    ).fit(x, y)
    model = nn.Sequential(
        nn.Linear(len(NAMES), 64),
        nn.ReLU(),
        nn.Linear(64, 32),
        nn.ReLU(),
        nn.Linear(32, 1),
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.002, weight_decay=0.001)
    inputs, targets, validation = (
        torch.tensor(x, dtype=torch.float32),
        torch.tensor(y),
        torch.tensor(v, dtype=torch.float32),
    )
    positive = torch.tensor(float((y == 0).sum() / max(1, (y == 1).sum())))
    best, state, stale, history = float("inf"), None, 0, []
    for epoch in range(160):
        model.train()
        for batch in torch.randperm(len(y)).split(256):
            optimizer.zero_grad()
            loss = nn.functional.binary_cross_entropy_with_logits(
                model(inputs[batch]).squeeze(1), targets[batch], pos_weight=positive
            )
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.inference_mode():
            loss = float(
                nn.functional.binary_cross_entropy_with_logits(
                    model(validation).squeeze(1), torch.tensor(vy)
                )
            )
        history.append(loss)
        if loss < best - 1e-5:
            best, state, stale = loss, copy.deepcopy(model.state_dict()), 0
        else:
            stale += 1
        if stale >= 20:
            break
    model.load_state_dict(state)
    model.eval()

    def logits(raw):
        with torch.inference_mode():
            return (
                model(torch.tensor((raw - mean) / scale, dtype=torch.float32))
                .squeeze(1)
                .numpy()
            )

    temp = temperature(logits(vx), vy)
    base_temp = temperature(logistic.decision_function(v), vy)
    val_scores = {
        "frozen_logistic": frozen.scores(np.stack(val.features), baseline=True),
        "frozen_mlp": frozen.scores(np.stack(val.features)),
        "timing_mlp": sigmoid(logits(vx) / temp),
        "timing_logistic": sigmoid(logistic.decision_function(v) / base_temp),
    }
    thresholds = {
        "frozen_logistic": (frozen.manifest["baseline_threshold"], None),
        "frozen_mlp": (frozen.manifest["threshold"], None),
        "frozen_mlp_safety": safety_threshold(vy, val_scores["frozen_mlp"]),
        "timing_mlp": safety_threshold(vy, val_scores["timing_mlp"]),
        "timing_logistic": safety_threshold(vy, val_scores["timing_logistic"]),
    }
    val_scores["frozen_mlp_safety"] = val_scores["frozen_mlp"]
    # Freeze candidate weights/thresholds BEFORE reading fresh holdout scores.
    torch.save(model.state_dict(), OUTPUT / "timing-mlp.pt")
    meta = {
        "feature_names": NAMES,
        "mean": mean.tolist(),
        "scale": scale.tolist(),
        "temperature": temp,
        "thresholds": thresholds,
        "baseline_coefficients": logistic.coef_[0].tolist(),
        "baseline_intercept": float(logistic.intercept_[0]),
        "baseline_temperature": base_temp,
        "epochs": len(history),
        "validation_bce_history": history,
        "weights_sha256": hashlib.sha256(
            (OUTPUT / "timing-mlp.pt").read_bytes()
        ).hexdigest(),
        "source_identity": source_identity(),
        "validation_metrics": {
            name: metrics(vy, scores, thresholds[name][0])
            for name, scores in val_scores.items()
        },
        "registered_by_training_command": False,
    }
    (OUTPUT / "candidate-manifest.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    fresh = pd.read_parquet(ROOT / "research/reliability/data/fresh-holdout.parquet")
    assert not set(fresh.input_hash) & set(old.input_hash)
    assert not set(fresh.physical_signature) & set(old.physical_signature)
    assert fresh.input_hash.is_unique
    report = {
        "protocol_commit": "70db480",
        "fresh_seed": 20261025,
        "fresh_rows": len(fresh),
        "fresh_dataset_sha256": hashlib.sha256(
            "\n".join(fresh.input_hash).encode()
        ).hexdigest(),
        "validation_only_selection": True,
        "old_test_not_pristine": True,
        "thresholds": thresholds,
        "splits": {},
        "promotion": {},
    }
    for split, rows in fresh.groupby("split"):
        scenarios = parse(rows)
        raw = np.stack([timing_features(s) for s in scenarios])
        labels = rows.failed.to_numpy()
        for row, s in zip(rows.itertuples(), scenarios, strict=True):
            actual = simulate(s)
            assert (
                actual.input_hash == row.input_hash
                and (not actual.summary.survived_full_window) == row.failed
            )
        scores = {
            "frozen_logistic": frozen.scores(np.stack(rows.features), baseline=True),
            "frozen_mlp": frozen.scores(np.stack(rows.features)),
            "timing_mlp": sigmoid(logits(raw) / temp),
            "timing_logistic": sigmoid(
                logistic.decision_function((raw - mean) / scale) / base_temp
            ),
        }
        scores["frozen_mlp_safety"] = scores["frozen_mlp"]
        subgroup = {
            "inverter_below_critical": np.array(
                [s.inverter.max_kw < s.load.critical_kw for s in scenarios]
            ),
            "no_islanding": np.array(
                [not s.inverter.islanding_capable for s in scenarios]
            ),
            "pv_available": np.array(
                [any(s.solar.profile_kw or [s.solar.generation_kw]) for s in scenarios]
            ),
            "mixed_grid_schedule": np.array(
                [
                    any(s.grid.profile_online or [s.grid.online])
                    and not all(s.grid.profile_online or [s.grid.online])
                    for s in scenarios
                ]
            ),
            "old_feature_range_ood": np.any(
                (np.stack(rows.features) < frozen.manifest["domain_min"])
                | (np.stack(rows.features) > frozen.manifest["domain_max"]),
                axis=1,
            ),
        }
        report["splits"][split] = {
            name: {
                "global": metrics(labels, p, thresholds[name][0]),
                "subgroups": {
                    g: metrics(labels[mask], p[mask], thresholds[name][0])
                    for g, mask in subgroup.items()
                    if mask.any()
                },
            }
            for name, p in scores.items()
        }

    def fpr(m):
        tn, fp = m["confusion_matrix"][0]
        return fp / max(1, tn + fp)

    for name in ["frozen_mlp_safety", "timing_mlp", "timing_logistic"]:
        gates = []
        for split, results in report["splits"].items():
            candidate, original, baseline = (
                results[name]["global"],
                results["frozen_mlp"]["global"],
                results["frozen_logistic"]["global"],
            )
            passed = (
                candidate["dangerous_recall"]
                >= max(original["dangerous_recall"], baseline["dangerous_recall"])
                and candidate["precision"] >= 0.80
                and fpr(candidate) <= fpr(original) + 0.03
                and candidate["f1"] >= original["f1"] - 0.02
                and candidate["brier_score"] <= original["brier_score"] + 0.02
            )
            gates.append(passed)
        report["promotion"][name] = all(gates)
    report["deployment_decision"] = (
        "Passing candidates require separate feature-contract/catalog replay in research.reliability.register; this training command performs no registration. Physics remains authoritative."
    )
    (OUTPUT / "comparison.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    print(
        json.dumps(
            {
                "epochs": len(history),
                "thresholds": thresholds,
                "promotion": report["promotion"],
                "results": {
                    s: {name: result["global"] for name, result in results.items()}
                    for s, results in report["splits"].items()
                },
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
