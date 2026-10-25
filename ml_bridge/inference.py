"""Checksum/source/feature-verified neural checkpoint. Imported only when requested."""

import hashlib
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn

from .features import (
    FEATURE_NAMES,
    FEATURE_SCHEMA,
    FEATURE_SHA256,
    features,
    feature_source_sha256,
)
from .runtime import source_identity


def feature_contract(schema):
    if schema == FEATURE_SCHEMA:
        return (
            FEATURE_NAMES,
            FEATURE_SCHEMA,
            FEATURE_SHA256,
            feature_source_sha256(),
            features,
        )
    from .timing_features import (
        NAMES,
        FEATURE_SCHEMA as TIMING_SCHEMA,
        FEATURE_SHA256 as TIMING_HASH,
        feature_source_sha256 as timing_source,
        timing_features,
    )

    if schema != TIMING_SCHEMA:
        raise ValueError("Unsupported feature schema")
    return NAMES, TIMING_SCHEMA, TIMING_HASH, timing_source(), timing_features


class FragilityNet(nn.Module):
    def __init__(self, input_size=len(FEATURE_NAMES)):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x):
        return self.layers(x).squeeze(-1)


class FragilityPredictor:
    def __init__(self, network, manifest):
        self.network, self.manifest = network.eval(), manifest
        self.mean, self.scale = (
            np.asarray(manifest["mean"]),
            np.asarray(manifest["scale"]),
        )
        self.feature_names, _, _, _, self.extract = feature_contract(
            manifest["feature_schema"]
        )

    @classmethod
    def load(cls, directory: Path, *, require_catalog=True):
        meta = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        names, schema, digest, source, _ = feature_contract(meta["feature_schema"])
        for key, expected in {
            **source_identity(),
            "feature_schema": schema,
            "feature_sha256": digest,
            "feature_names": names,
            "feature_source_sha256": source,
        }.items():
            if meta.get(key) != expected:
                raise ValueError(f"Checkpoint does not match {key}")
        if require_catalog:
            catalog = json.loads(
                (Path(__file__).parent / "verified_catalog.json").read_text(
                    encoding="utf-8"
                )
            )
            if catalog.get("catalog_version") != "lastlight-ml-artifact-catalog-1":
                raise ValueError("Unsupported artifact catalog contract")
            canonical = json.dumps(
                meta, sort_keys=True, separators=(",", ":"), allow_nan=False
            )
            entry = catalog.get("models", {}).get(meta["model_version"])
            if (
                not entry
                or entry["manifest_sha256"]
                != hashlib.sha256(canonical.encode()).hexdigest()
            ):
                raise ValueError(
                    "Checkpoint is not in the independently validated artifact catalog"
                )
        for key in [
            "mean",
            "scale",
            "domain_min",
            "domain_max",
            "baseline_coefficients",
        ]:
            values = np.asarray(meta[key], dtype=np.float64)
            if values.shape != (len(names),) or not np.isfinite(values).all():
                raise ValueError(
                    "Invalid checkpoint preprocessing dimensions or values"
                )
        if np.any(np.asarray(meta["scale"]) <= 0) or np.any(
            np.asarray(meta["domain_min"]) > np.asarray(meta["domain_max"])
        ):
            raise ValueError("Invalid normalization/domain bounds")
        for key in ["temperature", "baseline_temperature"]:
            if not np.isfinite(meta[key]) or meta[key] <= 0:
                raise ValueError("Invalid calibration temperature")
        for key in ["threshold", "baseline_threshold"]:
            if not np.isfinite(meta[key]) or not 0 <= meta[key] <= 1:
                raise ValueError("Invalid decision threshold")
        if not np.isfinite(meta["baseline_intercept"]):
            raise ValueError("Invalid baseline intercept")
        weights = directory / "model.pt"
        digest = hashlib.sha256(weights.read_bytes()).hexdigest()
        if (
            digest != meta["checkpoint_sha256"]
            or meta["model_version"]
            != f"fragility-official-v1-{'timing-' if schema.endswith('-2') else ''}{digest[:12]}"
        ):
            raise ValueError("Checkpoint integrity/identity mismatch")
        torch.set_num_threads(1)
        model = FragilityNet(len(names))
        model.load_state_dict(
            torch.load(weights, map_location="cpu", weights_only=True)
        )
        if any(
            not torch.isfinite(value).all() for value in model.state_dict().values()
        ):
            raise ValueError("Nonfinite network parameters")
        return cls(model, meta)

    def scores(self, matrix, baseline=False):
        raw = np.atleast_2d(matrix).astype(np.float64)
        if raw.shape[1] != len(self.feature_names) or not np.isfinite(raw).all():
            raise ValueError("Input feature contract mismatch")
        normalized = (raw - self.mean) / self.scale
        if baseline:
            logits = (
                normalized @ np.asarray(self.manifest["baseline_coefficients"])
                + self.manifest["baseline_intercept"]
            )
            temp = self.manifest["baseline_temperature"]
        else:
            with torch.inference_mode():
                logits = self.network(
                    torch.tensor(normalized, dtype=torch.float32)
                ).numpy()
            temp = self.manifest["temperature"]
        if not np.isfinite(logits).all():
            raise ValueError("Nonfinite network output")
        return 1 / (1 + np.exp(-np.clip(logits / temp, -40, 40)))

    def predict(self, scenario):
        vector = np.asarray(self.extract(scenario))
        score = float(self.scores(vector)[0])
        outside = bool(
            np.any(vector < np.asarray(self.manifest["domain_min"]) - 1e-6)
            or np.any(vector > np.asarray(self.manifest["domain_max"]) + 1e-6)
        )
        uncertain = abs(score - self.manifest["threshold"]) <= 0.05
        warnings = []
        if outside:
            warnings.append(
                "Outside observed training feature bounds. Range checks do not detect every distribution shift; use official physics."
            )
        if uncertain:
            warnings.append(
                "Near the fitted decision threshold: heuristic uncertainty flag, not a statistical confidence interval. Use official physics."
            )
        return {
            "predicted_failure": score >= self.manifest["threshold"],
            "synthetic_failure_score": score,
            "outside_training_domain": outside,
            "high_uncertainty": uncertain,
        }, warnings
