import argparse
import json
from pathlib import Path
import numpy as np
from ml.frontier import benchmark, DEFAULT_MODEL
from ml.models.fragility_net import FragilityPredictor
from services.simulation.schemas import SimulationRequest


def main():
    parser = argparse.ArgumentParser(
        description="Compare uniform, random, ML and exact trace frontiers."
    )
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ml/artifacts/fragility-v1/frontier-benchmark.json"),
    )
    args = parser.parse_args()
    predictor = FragilityPredictor.load(args.model)
    time = (np.arange(96) + 0.5) / 4
    solar = 3 * np.maximum(0, np.sin((time - 7) * np.pi / 11))
    solar[(time <= 7) | (time >= 18)] = 0
    variable = SimulationRequest.model_validate(
        {
            "duration_hours": 24,
            "solar": {"profile_kw": solar.tolist(), "islanding_capable": True},
            "load": {
                "critical_profile_kw": (1.5 + 0.4 * np.sin(time * np.pi / 12)).tolist()
            },
        }
    )
    result = {
        "battery_only": benchmark(SimulationRequest(duration_hours=24), predictor),
        "variable_profiles": benchmark(variable, predictor),
    }
    args.output.write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
