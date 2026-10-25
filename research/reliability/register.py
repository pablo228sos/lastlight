"""Register only the preregistered passing timing model, after independent replay."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ml_bridge.inference import FragilityNet, FragilityPredictor
from ml_bridge.runtime import source_identity
from ml_bridge.timing_features import (
    NAMES,
    FEATURE_SCHEMA,
    FEATURE_SHA256,
    feature_source_sha256,
    timing_features,
)
from research.reliability.features import timing_features as trained_features
from services.simulation.engine import simulate
from services.simulation.schemas import SimulationRequest

ROOT = Path(__file__).resolve().parents[2]


def main():
    torch.set_num_threads(1)
    research = ROOT / "research/reliability/artifacts"
    comparison = json.loads((research / "comparison.json").read_text())
    if not comparison["promotion"]["timing_mlp"]:
        raise ValueError("Preregistered timing-model promotion gate failed")
    config = json.loads((research / "candidate-manifest.json").read_text())
    old = pd.read_parquet(ROOT / "ml_bridge/data/generated/scenarios.parquet")
    fresh = pd.read_parquet(ROOT / "research/reliability/data/fresh-holdout.parquet")
    train = old[old.split == "train"]
    x = np.stack(
        [
            timing_features(SimulationRequest.model_validate_json(v))
            for v in train.parameters_json
        ]
    )
    target = ROOT / "ml_bridge/artifacts/fragility-official-v1-timing"
    target.mkdir(parents=True, exist_ok=True)
    state = torch.load(
        research / "timing-mlp.pt", map_location="cpu", weights_only=True
    )
    network = FragilityNet(len(NAMES))
    network.load_state_dict({"layers." + key: value for key, value in state.items()})
    torch.save(network.state_dict(), target / "model.pt")
    digest = hashlib.sha256((target / "model.pt").read_bytes()).hexdigest()
    meta = {
        **source_identity(),
        "feature_schema": FEATURE_SCHEMA,
        "feature_sha256": FEATURE_SHA256,
        "feature_names": NAMES,
        "feature_source_sha256": feature_source_sha256(),
        "model_version": "fragility-official-v1-timing-" + digest[:12],
        "checkpoint_sha256": digest,
        "mean": config["mean"],
        "scale": config["scale"],
        "domain_min": x.min(0).tolist(),
        "domain_max": x.max(0).tolist(),
        "temperature": config["temperature"],
        "threshold": config["thresholds"]["timing_mlp"][0],
        "baseline_temperature": config["baseline_temperature"],
        "baseline_threshold": config["thresholds"]["timing_logistic"][0],
        "baseline_coefficients": config["baseline_coefficients"],
        "baseline_intercept": config["baseline_intercept"],
        "training_rows": len(train),
        "seed": 20261025,
        "epochs": config["epochs"],
        "architecture": [len(NAMES), 64, 32, 1],
        "training_configuration": {
            "optimizer": "AdamW",
            "learning_rate": 0.002,
            "weight_decay": 0.001,
            "batch_size": 256,
            "max_epochs": 160,
            "patience": 20,
            "selection": "validation BCE; validation temperature; validation safety threshold",
        },
        "old_dataset_hash": hashlib.sha256(
            "\n".join(old.input_hash).encode()
        ).hexdigest(),
        "fresh_holdout_hash": comparison["fresh_dataset_sha256"],
        "preregistration_commit": "70db480",
        "provenance": "synthetic official-v1 scenarios only; not real-world outage probability",
        "promotion_criterion": "all preregistered recall/precision/FPR/F1/Brier criteria on both fresh groups",
    }
    (target / "manifest.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    loaded = FragilityPredictor.load(target, require_catalog=False)
    results = {}
    missed_cases = {}
    for split, rows in fresh.groupby("split"):
        raw = []
        for row in rows.itertuples():
            s = SimulationRequest.model_validate_json(row.parameters_json)
            actual = simulate(s)
            assert (
                actual.input_hash == row.input_hash
                and (not actual.summary.survived_full_window) == row.failed
            )
            a, b = timing_features(s), trained_features(s)
            np.testing.assert_array_equal(a, b)
            raw.append(a)
        scores = loaded.scores(np.stack(raw))
        from ml_bridge.metrics import metrics

        actual_metrics = metrics(rows.failed.to_numpy(), scores, meta["threshold"])
        expected = comparison["splits"][split]["timing_mlp"]["global"]
        for name in [
            "dangerous_recall",
            "false_negatives",
            "precision",
            "f1",
            "brier_score",
            "pr_auc",
        ]:
            assert np.isclose(
                actual_metrics[name], expected[name], rtol=1e-7, atol=1e-8
            )
        results[split] = actual_metrics
        missed_cases[split] = []
        for row, score in zip(rows.itertuples(), scores, strict=True):
            if row.failed and score < meta["threshold"]:
                physical = simulate(
                    SimulationRequest.model_validate_json(row.parameters_json)
                )
                index = next(
                    i
                    for i, point in enumerate(physical.trace)
                    if point.unserved_critical_kw > 1e-9
                )
                missed_cases[split].append(
                    {
                        "scenario_id": row.scenario_id,
                        "input_hash": row.input_hash,
                        "equipment_id": row.equipment_id,
                        "score": float(score),
                        "physical_summary": physical.summary.model_dump(mode="json"),
                        "trace_before_and_at_failure": [
                            point.model_dump(mode="json")
                            for point in physical.trace[max(0, index - 1) : index + 2]
                        ],
                    }
                )
    evidence = {
        "model_version": meta["model_version"],
        "fresh_official_replayed_rows": len(fresh),
        "registered_feature_count": len(NAMES),
        "fresh_holdout_hash": meta["fresh_holdout_hash"],
        "preregistered_gate_passed": True,
        "saved_weights_reproduce_final_metrics": True,
        "splits": results,
        "false_negative_cases": missed_cases,
    }
    (target / "independent-evaluation.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    catalog_path = ROOT / "ml_bridge/verified_catalog.json"
    catalog = json.loads(catalog_path.read_text())
    catalog["models"][meta["model_version"]] = {
        "manifest_sha256": hashlib.sha256(
            json.dumps(
                meta, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        ).hexdigest()
    }
    catalog_path.write_text(
        json.dumps(catalog, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    assert (
        FragilityPredictor.load(target).manifest["model_version"]
        == meta["model_version"]
    )
    print(json.dumps(evidence), flush=True)


if __name__ == "__main__":
    main()
