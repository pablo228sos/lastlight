"""Print the complete exact output of the documented design-search request.

Run at repo root: python -m services.simulation.design_example
This calls the exact same production validator and official design_search code.
"""
import json
from pathlib import Path

from .design_search import DesignSearchRequest, design_search


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    path = root / "docs/physics/examples/design-search.request.json"
    request = DesignSearchRequest.model_validate_json(path.read_text(encoding="utf-8"))
    result = design_search(request)
    print(json.dumps(result.model_dump(mode="json"), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
