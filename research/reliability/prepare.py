"""Regenerate exactly the preregistered holdout, without reading model scores."""

import hashlib
import json
from pathlib import Path

import pandas as pd

from ml_bridge.generate import generate_dataset
from ml_bridge.runtime import source_identity


def main():
    root = Path(__file__).resolve().parents[2]
    old = pd.read_parquet(root / "ml_bridge/data/generated/scenarios.parquet")
    generated = generate_dataset(6000, 20261025)
    holdout = generated[generated.split.isin(["test", "generalization"])]
    if set(holdout.input_hash) & set(old.input_hash) or set(
        holdout.physical_signature
    ) & set(old.physical_signature):
        raise ValueError("Fresh holdout duplicates original physical scenarios")
    output = root / "research/reliability/data"
    output.mkdir(parents=True, exist_ok=True)
    holdout.to_parquet(output / "fresh-holdout.parquet", index=False)
    manifest = {
        "preregistration_commit": "70db480",
        "generator_seed": 20261025,
        "generated_rows": 6000,
        "retained_rows": len(holdout),
        "retained_splits": holdout.groupby("split").size().to_dict(),
        "retained_capacity_groups": {
            name: sorted(rows.capacity_kwh.unique().tolist())
            for name, rows in holdout.groupby("split")
        },
        "input_hash_sequence_sha256": hashlib.sha256(
            "\n".join(holdout.input_hash).encode()
        ).hexdigest(),
        "no_original_physical_signature_overlap": True,
        **source_identity(),
    }
    target = root / "research/reliability/artifacts/holdout-manifest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
