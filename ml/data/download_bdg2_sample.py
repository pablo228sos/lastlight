"""Bounded reproducible research subset; never commits the overseas meter data."""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.request import urlopen

BDG2_REF = "9b97ccbe90096aff42ed4fd6493bf7ae692d7118"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hours", type=int, default=672)
    parser.add_argument("--buildings", type=int, default=12)
    parser.add_argument("--output", type=Path, default=Path("ml/data/raw/bdg2"))
    args = parser.parse_args()
    if not 336 <= args.hours <= 17544 or not 3 <= args.buildings <= 100:
        raise ValueError(
            "Bounded subset requires 336..17544 hours and 3..100 buildings"
        )
    args.output.mkdir(parents=True, exist_ok=True)
    base = f"https://media.githubusercontent.com/media/buds-lab/building-data-genome-project-2/{BDG2_REF}/data"
    with urlopen(base + "/metadata/metadata.csv", timeout=60) as response:
        metadata = response.read(2_000_001)
    if len(metadata) > 2_000_000:
        raise ValueError("Unexpected metadata size")
    (args.output / "metadata.csv").write_bytes(metadata)
    with urlopen(
        base + "/meters/cleaned/electricity_cleaned.csv", timeout=60
    ) as response:
        reader = csv.DictReader(io.TextIOWrapper(response, encoding="utf8"))
        if not reader.fieldnames or "timestamp" not in reader.fieldnames:
            raise ValueError(
                "Expected BDG2 electricity CSV, not a pointer or HTML response"
            )
        names = [x for x in reader.fieldnames if x != "timestamp"]
        selected = [
            names[round(i * (len(names) - 1) / (args.buildings - 1))]
            for i in range(args.buildings)
        ]
        with (args.output / "electricity-sample.csv").open(
            "w", newline="", encoding="utf8"
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=["timestamp"] + selected)
            writer.writeheader()
            count = 0
            for row in reader:
                writer.writerow({name: row[name] for name in ["timestamp"] + selected})
                count += 1
                if count >= args.hours:
                    break
    manifest = {
        "source_commit": BDG2_REF,
        "source_file": "data/meters/cleaned/electricity_cleaned.csv",
        "selection": "first hours; columns evenly spaced in source column order",
        "hours": count,
        "buildings": selected,
        "category": "overseas measured research data, not Kyrgyzstan",
        "sha256_of_local_subset": hashlib.sha256(
            (args.output / "electricity-sample.csv").read_bytes()
        ).hexdigest(),
    }
    (args.output / "source.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
