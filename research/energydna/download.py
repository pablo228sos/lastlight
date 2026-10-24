"""Download a bounded, pinned BDG2 raw-meter subset without full-series cleaning."""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.request import urlopen

REF = "9b97ccbe90096aff42ed4fd6493bf7ae692d7118"
BASE = f"https://media.githubusercontent.com/media/buds-lab/building-data-genome-project-2/{REF}"
BUILDINGS = [
    "Panther_parking_Lorriane",
    "Robin_lodging_Celia",
    "Fox_warehouse_Lorretta",
    "Rat_assembly_Francine",
    "Rat_assembly_Silvia",
    "Lamb_education_Emery",
    "Peacock_lodging_Mathew",
    "Bull_lodging_Leonard",
    "Swan_unknown_Isaiah",
    "Hog_education_Cathleen",
    "Eagle_health_Amy",
    "Mouse_science_Micheal",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download(output: Path, hours: int = 2160) -> dict:
    if not 672 <= hours <= 8760:
        raise ValueError("Bounded experiment requires 672..8760 hourly rows")
    output.mkdir(parents=True, exist_ok=True)
    urls = {
        "metadata.csv": BASE + "/data/metadata/metadata.csv",
        "electricity.csv": BASE + "/data/meters/raw/electricity.csv",
    }
    with urlopen(urls["metadata.csv"], timeout=60) as response:
        metadata = response.read(2_000_001)
    if len(metadata) > 2_000_000:
        raise ValueError("Unexpected metadata size")
    (output / "metadata.csv").write_bytes(metadata)
    with urlopen(urls["electricity.csv"], timeout=60) as response:
        reader = csv.DictReader(io.TextIOWrapper(response, encoding="utf8"))
        fields = ["timestamp", *BUILDINGS]
        if not set(fields) <= set(reader.fieldnames or []):
            raise ValueError("Expected pinned raw electricity columns, not LFS pointer")
        # Explicit LF bytes give the same subset checksum on Windows and Linux.
        with (output / "electricity.csv").open(
            "w", newline="", encoding="utf8"
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            count = 0
            for row in reader:
                writer.writerow({name: row[name] for name in fields})
                count += 1
                if count >= hours:
                    break
    if count != hours:
        raise ValueError("Upstream ended before the requested interval")
    manifest = {
        "dataset": "Building Data Genome 2",
        "source_commit": REF,
        "source_urls": urls,
        "source_file": "data/meters/raw/electricity.csv",
        "selection": "same 12 IDs as PR7; first requested hours, no outcome selection",
        "hours": count,
        "buildings": BUILDINGS,
        "sha256": {name: sha256(output / name) for name in urls},
        "input_units": "hourly electricity energy, kWh",
        "target_units": "average kW over next one-hour meter interval",
        "timestamp_basis": "source local hourly clock; naive, no UTC or weather join",
        "upstream_license": f"https://github.com/buds-lab/building-data-genome-project-2/blob/{REF}/LICENSE",
        "attribution": "Clayton Miller, Anjukan Kathirgamanathan, Balaji Picchetti et al., Building Data Genome Project 2 (2020), doi:10.1038/s41597-020-00712-x",
        "modifications": "12 raw electricity columns, bounded first hours; no retrospective cleaned-file filters",
        "category": "overseas whole-building research meters; not Kyrgyz critical circuits",
    }
    (output / "source.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("research/energydna/data"))
    parser.add_argument("--hours", type=int, default=2160)
    args = parser.parse_args()
    print(json.dumps(download(args.output, args.hours), indent=2))


if __name__ == "__main__":
    main()
