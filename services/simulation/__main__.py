"""Offline CLI: python -m services.simulation [simulate|compare] [input.json]."""

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from .engine import EnergyBalanceError, compare, simulate
from .schemas import ComparisonRequest, SimulationRequest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation", choices=["simulate", "compare"], nargs="?", default="simulate"
    )
    parser.add_argument(
        "input", type=Path, nargs="?", help="JSON request; defaults to {}"
    )
    args = parser.parse_args()
    try:
        content = args.input.read_text(encoding="utf-8-sig") if args.input else "{}"
        if args.operation == "simulate":
            result = simulate(SimulationRequest.model_validate_json(content))
        else:
            result = compare(ComparisonRequest.model_validate_json(content))
    except (OSError, ValidationError, EnergyBalanceError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result.model_dump(mode="json"), indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
