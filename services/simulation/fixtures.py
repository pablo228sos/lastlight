"""Generate/check frozen JSON contracts against the actual FastAPI endpoints.

Run from repository root: python -m services.simulation.fixtures [--check]
Requires requirements-dev.txt. No network, database, randomness or wall clock.
"""

import argparse
import json
from pathlib import Path

from fastapi.testclient import TestClient

from .api import app
from .schemas import ComparisonRequest, ComparisonResult, ErrorResponse, SimulationRequest, SimulationResult

FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "physics"


def artifacts() -> dict[str, dict]:
    baseline = SimulationRequest().model_dump(mode="json")
    comparison = ComparisonRequest().model_dump(mode="json")
    with TestClient(app) as client:
        def post(path: str, body: dict, status: int = 200) -> dict:
            response = client.post(path, json=body)
            if response.status_code != status:
                raise AssertionError(f"{path}: {response.status_code}: {response.text}")
            return response.json()

        response = post("/api/v1/simulations", baseline)
        assert response["summary"]["critical_survival_hours"] == 9.12
        assert response["summary"]["max_balance_residual_kwh"] < 1e-8
        return {
            "simulation-request.schema.json": SimulationRequest.model_json_schema(),
            "simulation-result.schema.json": SimulationResult.model_json_schema(),
            "comparison-request.schema.json": ComparisonRequest.model_json_schema(),
            "comparison-result.schema.json": ComparisonResult.model_json_schema(),
            "error.schema.json": ErrorResponse.model_json_schema(),
            "openapi.json": client.get("/openapi.json").json(),
            "fixtures/baseline.request.json": baseline,
            "fixtures/baseline.result.json": response,
            "fixtures/comparison.request.json": comparison,
            "fixtures/comparison.result.json": post("/api/v1/comparisons", comparison),
            "fixtures/validation-error.json": post(
                "/api/v1/simulations", {"battery": {"initial_soc": 1.1}}, 422
            ),
            "fixtures/regression-16h.json": {
                name: post("/api/v1/simulations", {"duration_hours": 16, "battery": battery})
                for name, battery in [
                    ("baseline", {}),
                    ("battery_36_kwh", {"capacity_kwh": 36}),
                    ("full_precharge", {"initial_soc": 1}),
                ]
            },
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail on drift; do not write files")
    args = parser.parse_args()
    changed = []
    for name, data in artifacts().items():
        path = FIXTURE_ROOT / name
        content = json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            changed.append(name)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
    if args.check and changed:
        raise SystemExit("Frozen contract/fixture drift: " + ", ".join(changed))
    print(f"{'Verified' if args.check else 'Generated'} {len(artifacts_names())} contract and fixture files")


def artifacts_names() -> list[str]:
    return [
        "simulation-request", "simulation-result", "comparison-request", "comparison-result",
        "error", "openapi", "baseline-request", "baseline-result", "comparison-request-fixture",
        "comparison-result-fixture", "validation-error", "regression-16h",
    ]


if __name__ == "__main__":
    main()
