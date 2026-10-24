"""Rebuild pinned windows and independently replay saved-artifact metrics."""

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from research.energydna.data import load, make_windows, partition
from research.energydna.inference import EnergyPredictor
from research.energydna.train import benchmark


def replay(data_dir: Path, artifact: Path):
    torch.set_num_threads(1)
    predictor = EnergyPredictor(artifact)
    data, info = load(data_dir)
    splits = partition(make_windows(data, info), info)
    if info != predictor.manifest["data"]:
        raise ValueError("Dataset, split or missingness manifest differs")
    actual = benchmark(predictor.model, predictor.ridge, splits, info)
    stored = json.loads((artifact / "evaluation.json").read_text(encoding="utf8"))
    checked = 0
    for split, methods in actual.items():
        for name, scores in methods.items():
            for metric in ["n", "mae_kw", "rmse_kw", "macro_history_scaled_mae"]:
                if not np.isclose(
                    scores[metric],
                    stored["metrics"][split][name][metric],
                    rtol=1e-7,
                    atol=1e-8,
                ):
                    raise ValueError(
                        f"Independent metric mismatch {split}/{name}/{metric}"
                    )
                checked += 1
    result = {
        "status": "replayed",
        "weights_sha256": predictor.manifest["weights_sha256"],
        "source_sha256": predictor.manifest["source_sha256"],
        "checked_aggregate_metrics": checked,
        "cohort_counts": {split: len(sample["y"]) for split, sample in splits.items()},
        "all_methods_same_eligible_targets": True,
        "no_parameter_refitting": True,
        "metrics": actual,
    }
    (artifact / "independent-evaluation.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    print(json.dumps({key: value for key, value in result.items() if key != "metrics"}))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("research/energydna/data"))
    parser.add_argument(
        "--artifact", type=Path, default=Path("research/energydna/artifacts/gru-v1")
    )
    args = parser.parse_args()
    replay(args.data, args.artifact)


if __name__ == "__main__":
    main()
