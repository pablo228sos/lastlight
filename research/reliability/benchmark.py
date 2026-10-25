"""Warm per-model features plus score latency; separate from dispatch/API timing."""

import json
from pathlib import Path
from time import perf_counter
import statistics

from ml_bridge.inference import FragilityPredictor
from services.simulation.schemas import SimulationRequest


def main():
    original = FragilityPredictor.load(
        Path("ml_bridge/artifacts/fragility-official-v1")
    )
    timing = FragilityPredictor.load(
        Path("ml_bridge/artifacts/fragility-official-v1-timing")
    )
    scenario = SimulationRequest(duration_hours=16)
    report = {
        "method": "100 serial CPU repetitions after warmup, input-only feature extraction plus normalized/calibrated score; no disk verification/HTTP/physics",
        "models": {},
    }
    for name, model, baseline in [
        ("frozen_logistic", original, True),
        ("frozen_mlp", original, False),
        ("timing_logistic", timing, True),
        ("timing_mlp", timing, False),
    ]:

        def run():
            return model.scores(model.extract(scenario), baseline=baseline)

        run()
        samples = []
        for _ in range(100):
            start = perf_counter()
            run()
            samples.append((perf_counter() - start) * 1000)
        report["models"][name] = {
            "median_ms": statistics.median(samples),
            "p95_ms": sorted(samples)[94],
        }
    Path("research/reliability/artifacts/latency.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    print(json.dumps(report))


if __name__ == "__main__":
    main()
