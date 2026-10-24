"""Generate Parquet from deterministic dispatch; never measured failure labels."""

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ml.features import FEATURE_NAMES, FEATURE_VERSION, features
from services.simulation import MODEL_VERSION
from services.simulation.engine import simulate
from services.simulation.schemas import SimulationRequest

GENERATOR_VERSION = "synthetic-equipment-groups-1"


def generate_dataset(count: int = 6000, seed: int = 20261024) -> pd.DataFrame:
    if not 120 <= count <= 100_000:
        raise ValueError(
            "count must be 120..100000; allow every equipment split to be represented"
        )
    rng = np.random.default_rng(seed)
    equipment = [
        (float(c), float(p)) for c in [6, 12, 18, 24, 36, 48] for p in [2, 4, 6, 8, 12]
    ]
    rng.shuffle(equipment)
    pools = {
        "train": equipment[:18],
        "validation": equipment[18:24],
        "test": equipment[24:],
        "generalization": [
            (float(c), float(p)) for c in [30, 42, 60] for p in [3, 7, 11]
        ],
    }
    schedule = ["train"] * 6 + [
        "validation",
        "test",
        "generalization",
        "generalization",
    ]
    rows, signatures = [], set()
    for i in range(count):
        split = schedule[i % 10]
        pool = pools[split]
        capacity, inverter = pool[(i // 10) % len(pool)]
        horizon = float(rng.choice([4, 8, 12, 16, 24]))
        n = int(horizon * 4)
        hour = int(rng.integers(0, 24))
        times = (hour + (np.arange(n) + 0.5) / 4) % 24
        constant = bool(rng.random() < 0.3)
        shape = np.ones(n) if constant else 1 + 0.3 * np.sin((times - 6) * np.pi / 12)
        if not constant:
            shape[int(rng.integers(0, n))] *= float(rng.uniform(1.3, 2.0))
        critical = rng.uniform(0.4, 6) * shape
        noncritical = rng.uniform(0, 5) * shape
        solar_peak = float(rng.choice([0, 2, 5, 10]))
        solar = solar_peak * np.clip(np.sin((times - 7) * np.pi / 11), 0, None)
        solar[(times <= 7) | (times >= 18)] = 0
        solar *= float(rng.choice([0.3, 0.65, 1]))
        body = {
            "start_utc": (
                datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=hour)
            ).isoformat(),
            "duration_hours": horizon,
            "seed": int(rng.integers(0, 2**32 - 1)),
            "battery": {
                "capacity_kwh": capacity,
                "initial_soc": float(rng.uniform(0.3, 1)),
                "minimum_soc": float(rng.choice([0.1, 0.2, 0.25])),
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
                "critical_profile_kw": critical.tolist(),
                "noncritical_profile_kw": noncritical.tolist(),
                "shed_noncritical_during_outage": bool(rng.random() > 0.3),
            },
            "solar": {
                "profile_kw": solar.tolist(),
                "islanding_capable": bool(rng.random() > 0.1),
            },
            "provenance": {
                "category": "synthetic",
                "references": ["docs/DATA_PROVENANCE.md"],
            },
        }
        request = SimulationRequest.model_validate(body)
        result = simulate(request)
        physical = request.model_dump(mode="json", exclude={"seed", "provenance"})
        signature = hashlib.sha256(
            json.dumps(physical, sort_keys=True).encode()
        ).hexdigest()
        if signature in signatures:
            raise RuntimeError(
                "Duplicate physical scenario; change generator, never duplicate split rows"
            )
        signatures.add(signature)
        rows.append(
            {
                "scenario_id": f"synthetic-{seed}-{i:06d}",
                "equipment_id": f"{capacity:g}kwh-{inverter:g}kw",
                "split": split,
                "seed": request.seed,
                "generator_seed": seed,
                "physics_version": MODEL_VERSION,
                "generator_version": GENERATOR_VERSION,
                "feature_version": FEATURE_VERSION,
                "input_hash": result.input_hash,
                "physical_signature": signature,
                "parameters_json": request.model_dump_json(),
                "provenance": "synthetic_simulation",
                "features": features(request).tolist(),
                "failed": not result.summary.survived_full_window,
                "first_failure_hours": result.summary.critical_survival_hours,
                "unserved_critical_kwh": result.summary.unserved_critical_kwh,
                "outcome_json": result.summary.model_dump_json(),
            }
        )
    return pd.DataFrame(rows)


def distribution(data: pd.DataFrame) -> dict:
    x = np.stack(data.features)
    return {
        "generator_version": GENERATOR_VERSION,
        "feature_version": FEATURE_VERSION,
        "physics_version": MODEL_VERSION,
        "rows": len(data),
        "dataset_hash": hashlib.sha256("".join(data.input_hash).encode()).hexdigest(),
        "splits": {
            name: {
                "rows": len(group),
                "failures": int(group.failed.sum()),
                "equipment": sorted(group.equipment_id.unique().tolist()),
            }
            for name, group in data.groupby("split")
        },
        "features": {
            name: {
                "minimum": float(x[:, i].min()),
                "median": float(np.median(x[:, i])),
                "maximum": float(x[:, i].max()),
            }
            for i, name in enumerate(FEATURE_NAMES)
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=6000)
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument(
        "--output", type=Path, default=Path("ml/data/generated/scenarios.parquet")
    )
    args = parser.parse_args()
    data = generate_dataset(args.count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_parquet(args.output, index=False)
    report = distribution(data)
    args.output.with_suffix(".distribution.json").write_text(
        json.dumps(report, indent=2), encoding="utf8"
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
