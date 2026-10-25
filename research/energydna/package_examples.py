"""Reproduce the small attributed historical windows. No predictions are saved."""

import json
from pathlib import Path
import pandas as pd
from research.energydna.data import load


def main():
    data, info = load(Path("research/energydna/data"))
    specs = [
        ("rat-march20", "Rat_assembly_Francine"),
        ("silvia-march20", "Rat_assembly_Silvia"),
        ("mouse-march20", "Mouse_science_Micheal"),
    ]
    target = pd.Timestamp("2016-03-20 12:00:00")
    index = data.index.get_loc(target)
    examples = [
        {
            "example_id": key,
            "building_id": building,
            "forecast_origin_local": str(target),
            "history_start_local": str(data.index[index - 168]),
            "history_kw": data[building].iloc[index - 168 : index].tolist(),
            "recorded_actual_kw": float(data.loc[target, building]),
        }
        for key, building in specs
    ]
    path = Path("research/energydna/examples/historical.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"source": info["source"], "examples": examples}, indent=2, allow_nan=False
        )
        + "\n",
        encoding="utf8",
        newline="\n",
    )
    from ml_bridge.forecast import EXAMPLES_SHA256
    from research.energydna.download import sha256

    if sha256(path) != EXAMPLES_SHA256:
        raise ValueError("Packaged source bytes differ from verified preview")
    print(
        "Reproduced 3 source-hashed windows and historical targets; no saved model predictions"
    )


if __name__ == "__main__":
    main()
