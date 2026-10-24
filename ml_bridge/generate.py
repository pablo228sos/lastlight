"""Generate official-v1-labelled scenarios with whole-capacity equipment holdouts."""

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from services.simulation.engine import simulate
from services.simulation.schemas import SimulationRequest
from .features import FEATURE_NAMES, FEATURE_SCHEMA, features
from .runtime import source_identity

GENERATOR_VERSION = "official-v1-capacity-holdouts-1"


def generate_dataset(count=9000, seed=20261024):
    if not 120 <= count <= 100000:
        raise ValueError("count must be 120..100000")
    identity = source_identity()
    rng = np.random.default_rng(seed)
    capacities = {
        "train": [6, 12, 24, 48],
        "validation": [18],
        "test": [36],
        "generalization": [30, 42, 60],
    }
    schedule = ["train"] * 6 + [
        "validation",
        "test",
        "generalization",
        "generalization",
    ]
    rows, seen = [], set()
    for i in range(count):
        split = schedule[i % 10]
        capacity = float(rng.choice(capacities[split]))
        inverter = float(
            rng.choice([3, 7, 11] if split == "generalization" else [2, 4, 6, 8, 12])
        )
        duration = float(rng.choice([4, 8, 12, 16, 24]))
        n = int(duration * 4)
        hour = int(rng.integers(0, 24))
        times = (hour + (np.arange(n) + 0.5) / 4) % 24
        minimum = float(rng.choice([0.1, 0.2, 0.25]))
        initial = minimum if rng.random() < 0.05 else float(rng.uniform(0.3, 1))
        solar_peak = float(rng.choice([0, 2, 5, 10]))
        solar = solar_peak * np.clip(np.sin((times - 7) * np.pi / 11), 0, None)
        solar[(times <= 7) | (times >= 18)] = 0
        solar *= float(rng.choice([0.3, 0.65, 1]))
        grid = np.zeros(n, dtype=bool)
        grid_mode = int(rng.choice([0, 1, 2, 3], p=[0.7, 0.1, 0.1, 0.1]))
        if grid_mode == 1:
            grid[:] = True
        elif grid_mode == 2:
            grid[int(rng.integers(1, n)) :] = True
        elif grid_mode == 3:
            grid[: int(rng.integers(1, n))] = True
        body = {
            "start_utc": (
                datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=hour)
            ).isoformat(),
            "duration_hours": duration,
            "seed": int(rng.integers(0, 2**32 - 1)),
            "battery": {
                "capacity_kwh": capacity,
                "initial_soc": initial,
                "minimum_soc": minimum,
                "charge_efficiency": float(rng.uniform(0.88, 0.98)),
                "discharge_efficiency": float(rng.uniform(0.88, 0.98)),
                "max_charge_kw": inverter * 0.75,
                "max_discharge_kw": inverter,
            },
            "inverter": {
                "max_kw": inverter,
                "islanding_capable": bool(rng.random() > 0.05),
            },
            "load": {
                "critical_kw": 0.0
                if rng.random() < 0.02
                else float(rng.uniform(0.4, 6)),
                "noncritical_kw": float(rng.uniform(0, 5)),
                "shed_noncritical_during_outage": bool(rng.random() > 0.3),
            },
            "solar": {
                "profile_kw": solar.tolist(),
                "islanding_capable": bool(rng.random() > 0.1),
            },
            "grid": {
                "profile_online": grid.tolist(),
                "import_limit_kw": float(rng.choice([2, 5, 10, 20])),
                "charge_battery": bool(rng.random() < 0.15),
            },
            "provenance": {
                "category": "synthetic",
                "references": ["docs/ml/FRAGILITY_V1_MODEL_CARD.md"],
            },
        }
        request = SimulationRequest.model_validate(body)
        result = simulate(request)
        physical = request.model_dump(mode="json", exclude={"seed", "provenance"})
        signature = hashlib.sha256(
            json.dumps(physical, sort_keys=True).encode()
        ).hexdigest()
        if signature in seen:
            raise ValueError("Duplicate physical scenario")
        seen.add(signature)
        rows.append(
            {
                "scenario_id": f"official-{seed}-{i:06d}",
                "equipment_id": f"{capacity:g}kwh-{inverter:g}kw",
                "capacity_kwh": capacity,
                "split": split,
                "seed": request.seed,
                "generator_seed": seed,
                **identity,
                "generator_version": GENERATOR_VERSION,
                "feature_schema": FEATURE_SCHEMA,
                "input_hash": result.input_hash,
                "physical_signature": signature,
                "parameters_json": request.model_dump_json(),
                "provenance": "synthetic_official_v1_simulation",
                "features": features(request),
                "failed": not result.summary.survived_full_window,
                "first_failure_hours": result.summary.critical_survival_hours,
                "unserved_critical_kwh": result.summary.unserved_critical_kwh,
                "outcome_json": result.summary.model_dump_json(),
            }
        )
    return pd.DataFrame(rows)


def distribution(data):
    matrix = np.stack(data.features)
    return {
        "generator_version": GENERATOR_VERSION,
        "feature_schema": FEATURE_SCHEMA,
        **source_identity(),
        "rows": len(data),
        "dataset_hash": hashlib.sha256("".join(data.input_hash).encode()).hexdigest(),
        "splits": {
            name: {
                "rows": len(rows),
                "failures": int(rows.failed.sum()),
                "capacities_kwh": sorted(rows.capacity_kwh.unique().tolist()),
                "equipment": sorted(rows.equipment_id.unique().tolist()),
            }
            for name, rows in data.groupby("split")
        },
        "features": {
            name: {
                "minimum": float(matrix[:, i].min()),
                "median": float(np.median(matrix[:, i])),
                "maximum": float(matrix[:, i].max()),
            }
            for i, name in enumerate(FEATURE_NAMES)
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=9000)
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ml_bridge/data/generated/scenarios.parquet"),
    )
    args = parser.parse_args()
    data = generate_dataset(args.count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_parquet(args.output, index=False)
    report = distribution(data)
    args.output.with_suffix(".distribution.json").write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "rows": len(data),
                "dataset_hash": report["dataset_hash"],
                "splits": report["splits"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
