"""Read pinned repository artifacts; audit their arithmetic without training ML.

Requires a local git clone containing PR6, PR7 and PR8 commit objects. Candidate
physics is executed only in a temporary directory and a separate Python process.
No checkout, branch, source file or model in that clone is changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHAS = {
    "official_physics_pr6": "ef23a710ecb7b235ea734171730a4656c40f4615",
    "candidate_ml_pr7": "7147b3f1d0808886c1ca7dc5954ba94edc1564bd",
    "integration_pr8": "92613f0b39eec32813a438883e7d4fca18bce0e2",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    repo = args.repository.resolve()
    source_hashes = {}

    def read(which: str, path: str) -> bytes:
        revision = SHAS[which]
        content = subprocess.check_output(
            ["git", "-C", str(repo), "show", revision + ":" + path]
        )
        source_hashes[revision + ":" + path] = hashlib.sha256(content).hexdigest()
        return content

    def artifact(path: str):
        return json.loads(read("candidate_ml_pr7", "ml/artifacts/fragility-v1/" + path))

    metrics = artifact("independent-test.json")
    arithmetic = {}
    for split, models in metrics.items():
        arithmetic[split] = {}
        for name, reported in models.items():
            (tn, fp), (fn, tp) = reported["confusion_matrix"]
            n = tn + fp + fn + tp
            calculated = {
                "n": n,
                "accuracy": (tn + tp) / n,
                "precision": tp / (tp + fp),
                "dangerous_recall": tp / (tp + fn),
                "f1": 2 * tp / (2 * tp + fp + fn),
                "false_negatives": fn,
            }
            assert reported["confusion_order"] == ["survives", "fails"]
            for key, value in calculated.items():
                assert math.isclose(reported[key], value, abs_tol=1e-12)
            calculated["always_fails_accuracy"] = (tp + fn) / n
            calculated["confusion_matrix"] = reported["confusion_matrix"]
            arithmetic[split][name] = calculated

    benchmark = artifact("frontier-benchmark.json")
    frontier = {}
    for case, data in benchmark.items():
        exact = data["methods"]["deterministic_trace"]
        ml = data["methods"]["ml_guided"]
        assert exact["mean_boundary_error_hours"] == exact["missed_unsafe_cells"] == 0
        frontier[case] = {
            "physics_version": data["physics_version"],
            "ml_model_version": data["model_version"],
            "deterministic_trace": exact,
            "ml_guided": ml,
            "ml_faster_than_exact_in_published_run": ml["seconds"] < exact["seconds"],
            "ml_more_accurate_than_exact_in_published_run": ml[
                "mean_boundary_error_hours"
            ]
            < exact["mean_boundary_error_hours"],
        }

    fixtures = {}
    for name in ["baseline", "comparison"]:
        official = read(
            "official_physics_pr6", f"docs/physics/fixtures/{name}.result.json"
        )
        integrated = read("integration_pr8", f"apps/web/src/data/{name}.result.json")
        assert official == integrated
        fixtures[name] = {
            "byte_identical_to_pr6": True,
            "sha256": hashlib.sha256(official).hexdigest(),
        }

    runtime_presence = {}
    files = ["__init__.py", "engine.py", "schemas.py"]
    for name in files:
        path = "services/simulation/" + name
        exists = (
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "cat-file",
                    "-e",
                    SHAS["integration_pr8"] + ":" + path,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        )
        runtime_presence[path] = exists

    # Reproduce the known PR7 exclusive-horizon edge case without importing its
    # ML package or treating its physics as the official study engine.
    with tempfile.TemporaryDirectory(prefix="lastlight-research-pr7-") as temporary:
        root = Path(temporary)
        directory = root / "services/simulation"
        directory.mkdir(parents=True)
        for name in files:
            (directory / name).write_bytes(
                read("candidate_ml_pr7", "services/simulation/" + name)
            )
        program = """
import json, sys
sys.path.insert(0, sys.argv[1])
from services.simulation.engine import simulate
from services.simulation.schemas import SimulationRequest
rows=[]
for step in [1,15,60]:
    result=simulate(SimulationRequest(duration_hours=9.12,step_minutes=step))
    rows.append({'step_minutes':step,'duration_hours':9.12,
        'first_failure_hours':result.summary.critical_survival_hours,
        'survived_full_window':result.summary.survived_full_window,
        'unserved_critical_kwh':result.summary.unserved_critical_kwh})
print(json.dumps(rows))
"""
        boundary = json.loads(
            subprocess.check_output(
                [sys.executable, "-c", program, str(root)], cwd=root, text=True
            )
        )

    report = {
        "snapshot_date": "2026-10-24",
        "commits": SHAS,
        "scope": "Published artifact arithmetic and fixture identity; no retraining, no field validation, no new ML benchmark timing.",
        "metric_arithmetic": arithmetic,
        "published_frontier_comparison": frontier,
        "pr8_fixtures": fixtures,
        "pr8_backend_source_present_in_frontend_checkout": runtime_presence,
        "pr8_live_demo_requires_separate_official_backend_checkout": True,
        "pr7_exclusive_horizon_reproduction": boundary,
        "source_sha256": source_hashes,
    }
    content = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    output = ROOT / "docs/research/data/repository_evidence_audit.json"
    if args.check:
        if not output.exists() or output.read_text(encoding="utf-8") != content:
            raise SystemExit("Repository evidence drift")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8", newline="\n")
    print(
        "Verified published metric arithmetic, two fixture pairs and PR7 boundary reproduction"
    )
    print(
        json.dumps(
            {"pr8_backend_source_present": runtime_presence, "pr7_boundary": boundary}
        )
    )


if __name__ == "__main__":
    main()
