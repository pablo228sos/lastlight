"""Verified research artifact reload and explicit one-hour forecast interface."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from research.energydna.data import FEATURE_VERSION, source_hash, window_features
from research.energydna.download import sha256
from research.energydna.model import EnergyDNA


class EnergyPredictor:
    def __init__(self, directory: Path):
        self.manifest = json.loads(
            (directory / "manifest.json").read_text(encoding="utf8")
        )
        if (
            self.manifest["feature_version"] != FEATURE_VERSION
            or self.manifest["source_sha256"] != source_hash()
            or self.manifest["horizon_hours"] != 1
        ):
            raise ValueError("Incompatible research source/feature/horizon contract")
        for filename, key in [
            ("model.pt", "weights_sha256"),
            ("ridge.json", "ridge_sha256"),
        ]:
            if sha256(directory / filename) != self.manifest[key]:
                raise ValueError(f"Artifact checksum mismatch: {filename}")
        if (
            self.manifest["model_version"]
            != "energydna-gru-v1-" + self.manifest["weights_sha256"][:12]
        ):
            raise ValueError("Model identity does not match weights")
        self.model = EnergyDNA()
        state = torch.load(
            directory / "model.pt", map_location="cpu", weights_only=True
        )
        if any(not torch.isfinite(value).all() for value in state.values()):
            raise ValueError("Nonfinite model weights")
        self.model.load_state_dict(state, strict=True)
        self.model.eval()
        self.ridge = json.loads((directory / "ridge.json").read_text(encoding="utf8"))

    def predict(
        self, history, target_start: pd.Timestamp, method="energydna_gru"
    ) -> float:
        """history[-1] is the interval immediately before target_start; source local clock."""
        target_start = pd.Timestamp(target_start)
        if target_start.tz is not None or target_start != target_start.floor("h"):
            raise ValueError("Naive source-local target hour required")
        sequence, static, ridge, scale = window_features(history, target_start)
        if method == "preferred":
            method = self.manifest["preferred_method"]
        if method == "energydna_gru":
            with torch.inference_mode():
                result = (
                    float(
                        self.model(
                            torch.tensor(sequence[None]), torch.tensor(static[None])
                        )[0]
                    )
                    * scale
                )
        elif method in {"seasonal_week", "seasonal_day", "persistence"}:
            result = (
                float(
                    static[
                        {"persistence": 0, "seasonal_day": 1, "seasonal_week": 2}[
                            method
                        ]
                    ]
                )
                * scale
            )
        elif method == "ridge":
            x = (ridge - np.array(self.ridge["mean"])) / np.array(self.ridge["scale"])
            result = (
                max(0.0, float(x @ self.ridge["coef"] + self.ridge["intercept"]))
                * scale
            )
        else:
            raise ValueError("Unknown forecasting method")
        if not np.isfinite(result):
            raise ValueError("Nonfinite forecast")
        return result


def main():
    import argparse
    from research.energydna.data import load

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact", type=Path, default=Path("research/energydna/artifacts/gru-v1")
    )
    parser.add_argument("--data", type=Path, default=Path("research/energydna/data"))
    parser.add_argument("--building", required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    data, _ = load(args.data)
    target = pd.Timestamp(args.target)
    if target not in data.index or args.building not in data:
        raise ValueError("Unknown source building or target hour")
    index = data.index.get_loc(target)
    if index < 168:
        raise ValueError("Insufficient 168-hour context")
    history = data[args.building].iloc[index - 168 : index].to_numpy()
    predictor = EnergyPredictor(args.artifact)
    print(
        json.dumps(
            {
                "target": str(target),
                "horizon_hours": 1,
                "units": "whole-building average kW",
                "neural_estimate": predictor.predict(history, target),
                "preferred_method": predictor.manifest["preferred_method"],
                "preferred_estimate": predictor.predict(history, target, "preferred"),
                "model_version": predictor.manifest["model_version"],
                "research_only": True,
            }
        )
    )


if __name__ == "__main__":
    main()
