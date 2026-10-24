"""Independent compatibility audit of unmodified PR #7 research against official v1."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
from pydantic import ValidationError

from services.simulation.engine import simulate
from services.simulation.schemas import SimulationRequest
from .metrics import metrics
from .runtime import source_identity


def audit(legacy_root: Path, data_path: Path):
    data = pd.read_parquet(data_path)
    # Use the original loader in its original 1.1 runtime, without changing metadata.
    code = """import json,sys,numpy as np,pandas as pd
from ml.models.fragility_net import FragilityPredictor
from services.simulation.engine import simulate
from services.simulation.schemas import SimulationRequest
p=FragilityPredictor.load('ml/artifacts/fragility-v1')
d=pd.read_parquet(sys.argv[1])
boundaries=[]
for step in [1,15,60]:
 for horizon in [9.119,9.12,9.120001]:
  r=simulate(SimulationRequest(duration_hours=horizon,step_minutes=step))
  boundaries.append({'step_minutes':step,'duration_hours':horizon,'survived_full_window':r.summary.survived_full_window,'first_failure_hours':r.summary.critical_survival_hours})
print(json.dumps({'model_version':p.metadata['model_version'],'physics_version':p.metadata['physics_version'],'threshold':p.metadata['threshold'],'scores':p.scores(np.stack(d.features)).tolist(),'boundaries':boundaries}))
"""
    legacy = subprocess.run(
        [sys.executable, "-c", code, str(data_path.resolve())],
        cwd=legacy_root,
        capture_output=True,
        text=True,
        check=True,
    )
    original = json.loads(legacy.stdout)
    rejected, mapped, disagreements = 0, [], 0
    for i, row in enumerate(data.itertuples()):
        body = json.loads(row.parameters_json)
        try:
            SimulationRequest.model_validate(body)
        except ValidationError:
            rejected += 1
        profiles = [
            body["load"].get(key)
            for key in ["critical_profile_kw", "noncritical_profile_kw"]
        ]
        if any(profile is not None and np.ptp(profile) > 1e-10 for profile in profiles):
            continue
        for scalar, key, profile in zip(
            ["critical_kw", "noncritical_kw"],
            ["critical_profile_kw", "noncritical_profile_kw"],
            profiles,
        ):
            body["load"].pop(key, None)
            if profile is not None:
                body["load"][scalar] = float(profile[0])
        request = SimulationRequest.model_validate(body)
        result = simulate(request)
        failed = not result.summary.survived_full_window
        disagreements += failed != row.failed
        mapped.append(
            {"split": row.split, "failed": failed, "score": original["scores"][i]}
        )
    overlap = pd.DataFrame(mapped)
    boundaries = []
    for old in original["boundaries"]:
        current = simulate(
            SimulationRequest(
                duration_hours=old["duration_hours"], step_minutes=old["step_minutes"]
            )
        )
        boundaries.append(
            {
                "step_minutes": old["step_minutes"],
                "duration_hours": old["duration_hours"],
                "legacy_survives": old["survived_full_window"],
                "official_survives": current.summary.survived_full_window,
                "legacy_first_failure": old["first_failure_hours"],
                "official_first_failure": current.summary.critical_survival_hours,
            }
        )
    return {
        "official": source_identity(),
        "legacy_model_version": original["model_version"],
        "legacy_physics_version": original["physics_version"],
        "legacy_checkpoint_sha256": hashlib.sha256(
            (legacy_root / "ml/artifacts/fragility-v1/model.pt").read_bytes()
        ).hexdigest(),
        "legacy_rows": len(data),
        "strict_v1_request_rejections": rejected,
        "constant_profile_projection_rows": len(overlap),
        "projected_label_disagreements": int(disagreements),
        "projected_holdout_metrics": {
            name: metrics(rows.failed, rows.score, original["threshold"])
            for name, rows in overlap[
                overlap.split.isin(["test", "generalization"])
            ].groupby("split")
        },
        "exclusive_horizon_cases": boundaries,
        "decision": "retrain_on_official_v1",
        "limitations": [
            "Constant profile projection is an explicitly restricted audit, not an official request compatibility adapter.",
            "Variable-load research inputs cannot be represented by official v1 without changing their meaning.",
            "Old feature extraction depends on 1.1 load fields and omits some official grid controls.",
            "An old model score or 93% research figure does not validate a new production checkpoint.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-root", type=Path, required=True)
    parser.add_argument("--legacy-data", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ml_bridge/artifacts/legacy-compatibility.json"),
    )
    args = parser.parse_args()
    report = audit(args.legacy_root, args.legacy_data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key not in ["projected_holdout_metrics", "limitations"]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
