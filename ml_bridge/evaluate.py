"""Independent official replay, held-out evaluation and explicit artifact registration."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from services.simulation.engine import simulate
from services.simulation.schemas import SimulationRequest
from .features import features
from .generate import distribution
from .inference import FragilityPredictor
from .metrics import metrics
from .runtime import source_identity


def evaluate(data, directory: Path, *, replay=True):
    model = FragilityPredictor.load(directory, require_catalog=False)
    if distribution(data)["dataset_hash"] != model.manifest["dataset_hash"]:
        raise ValueError("Independent evaluation data identity mismatch")
    replayed = 0
    if replay:
        for row in data.itertuples():
            request = SimulationRequest.model_validate_json(row.parameters_json)
            actual = simulate(request)
            if (
                actual.input_hash != row.input_hash
                or actual.summary.model_dump_json() != row.outcome_json
                or (not actual.summary.survived_full_window) != row.failed
                or not np.allclose(features(request), row.features, rtol=0, atol=1e-12)
            ):
                raise ValueError(
                    "Official replay or input-only feature identity failed"
                )
            replayed += 1
    report = {
        "model_version": model.manifest["model_version"],
        **source_identity(),
        "dataset_hash": model.manifest["dataset_hash"],
        "official_replayed_rows": replayed,
        "synthetic_labels_only": True,
        "splits": {},
    }
    for name, rows in data[data.split.isin(["test", "generalization"])].groupby(
        "split"
    ):
        x, y = np.stack(rows.features), rows.failed.to_numpy()
        scores = model.scores(x)
        details, causes = [], Counter()
        missed = rows[y & (scores < model.manifest["threshold"])]
        for row in missed.itertuples():
            request = SimulationRequest.model_validate_json(row.parameters_json)
            actual = simulate(request)
            point = next(p for p in actual.trace if p.status == "critical_failure")
            cause = (
                "battery_minimum_reached"
                if point.battery_soc <= request.battery.minimum_soc + 1e-9
                else "islanding_unavailable"
                if not point.grid_online and not request.inverter.islanding_capable
                else "available_power_below_critical_demand"
            )
            causes[cause] += 1
            if len(details) < 12:
                details.append(
                    {
                        "scenario_id": row.scenario_id,
                        "equipment_id": row.equipment_id,
                        "first_failure_hours": actual.summary.critical_survival_hours,
                        "unserved_critical_kwh": actual.summary.unserved_critical_kwh,
                        "trace_diagnostic": cause,
                        "parameters": request.model_dump(mode="json"),
                    }
                )
        report["splits"][name] = {
            "fragility_net": metrics(y, scores, model.manifest["threshold"]),
            "baseline": metrics(
                y, model.scores(x, baseline=True), model.manifest["baseline_threshold"]
            ),
            "false_negative_trace_diagnostics": dict(causes),
            "false_negative_examples": details,
        }
    report["boundary_cases"] = []
    for step in [1, 15, 60]:
        for horizon in [9.119, 9.12, 9.120001]:
            result = simulate(
                SimulationRequest(duration_hours=horizon, step_minutes=step)
            )
            expected = horizon <= 9.12
            if result.summary.survived_full_window != expected:
                raise ValueError("Official exclusive-horizon regression failed")
            report["boundary_cases"].append(
                {
                    "step_minutes": step,
                    "duration_hours": horizon,
                    "survived_full_window": result.summary.survived_full_window,
                    "first_failure_hours": result.summary.critical_survival_hours,
                }
            )
    return report


def register(directory: Path, report: dict, catalog_path: Path):
    if report["official_replayed_rows"] <= 0:
        raise ValueError("Registration requires independent official replay")
    meta = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    canonical = json.dumps(meta, sort_keys=True, separators=(",", ":"), allow_nan=False)
    report_path = directory / "independent-evaluation.json"
    report_path.write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )
    catalog = {
        "catalog_version": "lastlight-ml-artifact-catalog-1",
        "models": {
            meta["model_version"]: {
                "manifest_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
                "checkpoint_sha256": meta["checkpoint_sha256"],
                "validation": "independent official replay; not engineering certification",
                "replayed_rows": report["official_replayed_rows"],
                **source_identity(),
            }
        },
    }
    catalog_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data", type=Path, default=Path("ml_bridge/data/generated/scenarios.parquet")
    )
    parser.add_argument(
        "--model", type=Path, default=Path("ml_bridge/artifacts/fragility-official-v1")
    )
    parser.add_argument(
        "--register",
        action="store_true",
        help="Write the reviewed-code artifact catalog after full replay",
    )
    args = parser.parse_args()
    report = evaluate(pd.read_parquet(args.data), args.model)
    if args.register:
        register(args.model, report, Path(__file__).parent / "verified_catalog.json")
    else:
        (args.model / "independent-evaluation.json").write_text(
            json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
        )
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "splits"}, indent=2
        )
    )
    print(
        json.dumps(
            {
                name: {
                    key: value
                    for key, value in entry.items()
                    if not key.startswith("false_negative")
                }
                for name, entry in report["splits"].items()
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
