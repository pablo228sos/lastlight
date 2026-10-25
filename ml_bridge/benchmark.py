"""Measured cold-process and warm execution workloads; no Frontier speedup claim."""

import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys
from time import perf_counter


def setup(case):
    from services.simulation.schemas import SimulationRequest

    scenario = SimulationRequest(duration_hours=16)
    if case == "physics":
        from services.simulation.engine import simulate

        return lambda: simulate(scenario)
    if case in ["neural", "assessment"]:
        from ml_bridge.adapter import analyze_neural, assess, DEFAULT_CHECKPOINT
        from ml_bridge.contracts import AssessmentRequest

        directory = DEFAULT_CHECKPOINT.parent / "fragility-official-v1-timing"
        if case == "neural":
            return lambda: analyze_neural(
                scenario, directory, "lastlight-official-v1-features-2"
            )
        return lambda: assess(
            AssessmentRequest(
                scenario=scenario, feature_schema="lastlight-official-v1-features-2"
            ),
            directory,
        )
    if case in ["frontier", "candidates"]:
        from services.simulation.frontier import physics_frontier, FrontierRequest

        if case == "frontier":
            return lambda: physics_frontier(
                FrontierRequest(scenario=scenario, maximum_hours=16)
            )
        from ml_bridge.candidates import suggest
        from ml_bridge.contracts import CandidateRequest
        from ml_bridge.adapter import DEFAULT_CHECKPOINT

        physical = physics_frontier(
            FrontierRequest(scenario=scenario, maximum_hours=16)
        )
        points = [
            {k: p[k] for k in ["initial_soc", "duration_hours"]}
            for p in physical["trace"]
        ]
        request = CandidateRequest(
            scenario=scenario,
            points=points,
            limit=12,
            feature_schema="lastlight-official-v1-features-2",
        )
        return lambda: suggest(
            request, DEFAULT_CHECKPOINT.parent / "fragility-official-v1-timing"
        )
    if case == "forecast":
        from ml_bridge.forecast import forecast, ForecastRequest

        return lambda: forecast(ForecastRequest())
    raise ValueError(case)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cold-case")
    args = parser.parse_args()
    if args.cold_case:
        start = perf_counter()
        run = setup(args.cold_case)
        run()
        print(json.dumps({"ms": (perf_counter() - start) * 1000}))
        return
    report = {
        "environment": "local Windows CPU Python3.12; no browser rendering included",
        "cold_definition": "new Python subprocess; timer includes package imports, feature setup and first result; OS file cache not flushed",
        "warm_definition": "20 serial calls after one warmup; same real request/artifacts; excludes HTTP transport/JSON",
        "workloads": {},
    }
    for case in [
        "physics",
        "neural",
        "assessment",
        "frontier",
        "candidates",
        "forecast",
    ]:
        cold = []
        for _ in range(3):
            process = subprocess.run(
                [sys.executable, "-m", "ml_bridge.benchmark", "--cold-case", case],
                text=True,
                capture_output=True,
                check=True,
            )
            cold.append(json.loads(process.stdout)["ms"])
        run = setup(case)
        run()
        times = []
        for _ in range(20):
            start = perf_counter()
            run()
            times.append((perf_counter() - start) * 1000)
        report["workloads"][case] = {
            "cold_import_first_ms": cold,
            "cold_median_ms": statistics.median(cold),
            "warm_median_ms": statistics.median(times),
            "warm_p95_ms": sorted(times)[18],
            "warm_min_ms": min(times),
            "repetitions": 20,
        }
    report["workload_limits"] = {
        "physics": "one 16h official simulation, 15-minute base intervals",
        "neural": "verified timing checkpoint with input features/cache integrity and score, no physical run",
        "assessment": "one simulation plus verified timing neural analysis",
        "frontier": "13 official traces classify 273 cells",
        "candidates": "scores 273 supplied points and independently simulates 12 selected cases; cold setup also constructs the map to supply points",
        "forecast": "actual packaged 168h history, real one-hour GRU plus persistence and provenance",
    }
    report["interpretation"] = (
        "Different output workloads, not a comparable ML acceleration benchmark. Do not claim candidates accelerate the exact Frontier."
    )
    path = Path("docs/unified/performance.json")
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8", newline="\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
