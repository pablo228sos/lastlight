"""Small CPU MLP and safe, versioned inference; physics remains authoritative."""

import hashlib
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn

from ml.features import FEATURE_NAMES, FEATURE_VERSION, features
from services.simulation.schemas import SimulationRequest
from services.simulation import MODEL_VERSION


class FragilityNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(len(FEATURE_NAMES), 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x):
        return self.layers(x).squeeze(-1)


class FragilityPredictor:
    def __init__(self, network, metadata):
        self.network, self.metadata = network.eval(), metadata
        self.mean = np.asarray(metadata["mean"])
        self.scale = np.asarray(metadata["scale"])

    @classmethod
    def load(cls, directory: str | Path):
        directory = Path(directory)
        meta = json.loads((directory / "metadata.json").read_text(encoding="utf8"))
        if (
            meta["feature_version"] != FEATURE_VERSION
            or meta["feature_names"] != FEATURE_NAMES
        ):
            raise ValueError("Unsupported model preprocessing contract")
        if meta["physics_version"] != MODEL_VERSION:
            raise ValueError("Training labels belong to a different physics version")
        weights = directory / "model.pt"
        if (
            hashlib.sha256(weights.read_bytes()).hexdigest()
            != meta["checkpoint_sha256"]
        ):
            raise ValueError("Model checkpoint checksum mismatch")
        network = FragilityNet()
        network.load_state_dict(
            torch.load(weights, map_location="cpu", weights_only=True)
        )
        return cls(network, meta)

    def scores(self, matrix: np.ndarray, baseline=False) -> np.ndarray:
        matrix = np.atleast_2d(matrix).astype(np.float64)
        if matrix.shape[1] != len(FEATURE_NAMES) or not np.isfinite(matrix).all():
            raise ValueError("Features must be finite and match the versioned shape")
        x = (matrix - self.mean) / self.scale
        if baseline:
            logits = (
                x @ np.asarray(self.metadata["baseline_coefficients"])
                + self.metadata["baseline_intercept"]
            )
            temperature = self.metadata["baseline_temperature"]
        else:
            with torch.inference_mode():
                logits = self.network(torch.tensor(x, dtype=torch.float32)).numpy()
            temperature = self.metadata["temperature"]
        return 1 / (1 + np.exp(-np.clip(logits / temperature, -40, 40)))

    def predict_features(self, vector: np.ndarray) -> dict:
        vector = np.asarray(vector, dtype=np.float64)
        score = float(self.scores(vector)[0])
        outside = bool(
            np.any(vector < np.asarray(self.metadata["domain_min"]) - 1e-6)
            or np.any(vector > np.asarray(self.metadata["domain_max"]) + 1e-6)
        )
        uncertain = abs(score - 0.5) < 0.15
        warnings = [
            "Score is conditional on synthetic simulation labels, not real-world outage probability."
        ]
        if outside:
            warnings.append(
                "Outside observed training feature bounds; use physics evaluation."
            )
        if uncertain:
            warnings.append("High model uncertainty; use physics evaluation.")
        return {
            "model_version": self.metadata["model_version"],
            "synthetic_failure_score": score,
            "predicted_failure": score >= self.metadata["threshold"],
            "baseline_failure_score": float(self.scores(vector, baseline=True)[0]),
            "outside_training_domain": outside,
            "high_uncertainty": uncertain,
            "physics_required": True,
            "engineering_clearance": False,
            "warnings": warnings,
        }

    def predict(self, request: SimulationRequest) -> dict:
        result = self.predict_features(features(request))
        if request.step_minutes != 15 or request.grid.charge_battery:
            result["outside_training_domain"] = True
            result["warnings"].append(
                "Sampling/grid charging configuration not represented in training."
            )
        return result
