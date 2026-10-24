"""Independent held-out evaluation of an existing, checksum-verified checkpoint."""

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from ml.evaluation.metrics import metrics
from ml.models.fragility_net import FragilityPredictor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data", type=Path, default=Path("ml/data/generated/scenarios.parquet")
    )
    parser.add_argument("--model", type=Path, default=Path("ml/artifacts/fragility-v1"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = pd.read_parquet(args.data)
    predictor = FragilityPredictor.load(args.model)
    report = {}
    for name, rows in data[data.split.isin(["test", "generalization"])].groupby(
        "split"
    ):
        x = np.stack(rows.features)
        report[name] = {
            key: metrics(
                rows.failed,
                predictor.scores(x, baseline=baseline),
                predictor.metadata[threshold],
            )
            for key, baseline, threshold in [
                ("fragility_net", False, "threshold"),
                ("baseline", True, "baseline_threshold"),
            ]
        }
    content = json.dumps(report, indent=2, allow_nan=False)
    if args.output:
        args.output.write_text(content, encoding="utf8")
    print(content)


if __name__ == "__main__":
    main()
