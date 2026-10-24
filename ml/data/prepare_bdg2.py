"""BDG2 electricity preparation. Timestamp basis and meter units are explicit."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


def prepare(
    meters: pd.DataFrame,
    metadata: pd.DataFrame,
    *,
    meter: str,
    unit: str,
    timestamp_mode: str,
) -> tuple[pd.DataFrame, dict]:
    if meter != "electricity" or unit != "kWh":
        raise ValueError(
            "This pipeline accepts hourly electricity energy sums in kWh only"
        )
    if timestamp_mode not in {"utc", "local_standard", "local_wall"}:
        raise ValueError("Choose a verified timestamp basis; it is never inferred")
    if (
        not {"building_id", "timezone"} <= set(metadata.columns)
        or metadata.building_id.duplicated().any()
    ):
        raise ValueError("Unique building_id and timezone metadata are required")
    if "timestamp" not in meters or meters.timestamp.duplicated().any():
        raise ValueError("Unique hourly timestamp column required")
    raw_times = pd.DatetimeIndex(pd.to_datetime(meters.timestamp, errors="raise"))
    buildings = sorted(set(meters.columns) - {"timestamp"})
    if not set(buildings) <= set(metadata.building_id):
        raise ValueError("A meter has no matching building metadata")
    if len(buildings) < 3:
        raise ValueError(
            "At least three buildings needed for independent building splits"
        )
    groups = np.random.default_rng(20261024).permutation(buildings).tolist()
    train_end = max(1, int(len(groups) * 0.6))
    val_end = max(train_end + 1, int(len(groups) * 0.8))
    splits = {
        name: ("train" if i < train_end else "validation" if i < val_end else "test")
        for i, name in enumerate(groups)
    }
    rows = []
    quality = {
        "missing_readings": 0,
        "invalid_readings": 0,
        "ambiguous_or_nonexistent_times": 0,
        "inserted_gap_hours": 0,
    }
    meta = metadata.set_index("building_id")
    for name in buildings:
        zone = str(meta.loc[name, "timezone"])
        if timestamp_mode == "utc":
            stamps = (
                raw_times.tz_localize("UTC")
                if raw_times.tz is None
                else raw_times.tz_convert("UTC")
            )
        elif raw_times.tz is not None:
            raise ValueError("Local meter basis requires naive input timestamps")
        elif timestamp_mode == "local_wall":
            stamps = raw_times.tz_localize(
                zone, ambiguous="NaT", nonexistent="NaT"
            ).tz_convert("UTC")
        else:
            # Standard-time meters do not follow DST. Require this policy explicitly.
            years = set(raw_times.year)
            if len(years) != 1:
                offsets = {
                    min(
                        datetime(y, m, 1, tzinfo=ZoneInfo(zone)).utcoffset()
                        for m in [1, 7]
                    )
                    for y in years
                }
                if len(offsets) != 1:
                    raise ValueError(
                        "Historical standard UTC offset changes; process years separately"
                    )
            offset = min(
                datetime(
                    int(raw_times.year[0]), m, 1, tzinfo=ZoneInfo(zone)
                ).utcoffset()
                for m in [1, 7]
            )
            stamps = raw_times.tz_localize(timezone(offset)).tz_convert("UTC")
        values = pd.to_numeric(meters[name], errors="coerce").astype(float)
        quality["missing_readings"] += int(values.isna().sum())
        invalid = (values < 0) | ~np.isfinite(values) & values.notna()
        quality["invalid_readings"] += int(invalid.sum())
        values = values.mask(invalid)
        valid_time = ~stamps.isna()
        quality["ambiguous_or_nonexistent_times"] += int((~valid_time).sum())
        series = pd.Series(
            values.to_numpy()[valid_time], index=stamps[valid_time]
        ).sort_index()
        if series.index.duplicated().any():
            raise ValueError("Time conversion produced duplicate hours")
        full_index = pd.date_range(series.index.min(), series.index.max(), freq="h")
        quality["inserted_gap_hours"] += len(full_index) - len(series)
        series = series.reindex(full_index)
        # Hourly kWh / 1 hour = average kW; no unit conversion is applied to water/other meters.
        frame = pd.DataFrame(
            {
                "timestamp_utc": full_index,
                "building_id": name,
                "demand_kw": series.to_numpy(),
                "is_missing": series.isna().to_numpy(),
                "split": splits[name],
                "primaryspaceusage": str(
                    meta.loc[name].get("primaryspaceusage", "unknown")
                ),
            }
        )
        local = full_index.tz_convert(zone)
        frame["hour_local"] = local.hour
        frame["day_of_week"] = local.day_of_week
        frame["hour_sin"] = np.sin(local.hour * 2 * np.pi / 24)
        frame["hour_cos"] = np.cos(local.hour * 2 * np.pi / 24)
        frame["lag_24_kw"] = series.shift(24).to_numpy()
        frame["lag_168_kw"] = series.shift(168).to_numpy()
        frame["provenance"] = (
            "BDG2 overseas measured meters; forecasts are research-derived"
        )
        rows.append(frame)
    clean = pd.concat(rows, ignore_index=True)
    report = {
        "source": "Building Data Genome 2",
        "meter": "electricity",
        "input_unit": "kWh per hour",
        "output_unit": "average kW",
        "timestamp_basis": timestamp_mode,
        "output_timezone": "UTC",
        "buildings": len(buildings),
        "rows": len(clean),
        "quality": quality,
        **quality,
        "splits": {
            split: sorted(group.building_id.unique().tolist())
            for split, group in clean.groupby("split")
        },
        "policy": "No target imputation; gaps retained; lags use only observed past hours.",
        "not_kyrgyzstan_measurements": True,
    }
    return clean, report


def evaluate_baselines(clean: pd.DataFrame) -> dict:
    train = clean[clean.split == "train"].dropna(subset=["demand_kw"])
    profile = train.groupby(["primaryspaceusage", "hour_local"]).demand_kw.mean()
    global_profile = train.groupby("hour_local").demand_kw.mean()
    test = clean[clean.split == "test"].dropna(subset=["demand_kw"])
    cold = np.array(
        [
            profile.get(
                (row.primaryspaceusage, row.hour_local),
                global_profile.get(row.hour_local, train.demand_kw.mean()),
            )
            for row in test.itertuples()
        ]
    )
    history = []
    for _, rows in clean.groupby("building_id"):
        cutoff = (
            rows.timestamp_utc.min()
            + (rows.timestamp_utc.max() - rows.timestamp_utc.min()) * 0.8
        )
        history.append(
            rows[rows.timestamp_utc >= cutoff].dropna(
                subset=["demand_kw", "lag_168_kw"]
            )
        )
    historical = pd.concat(history)

    def score(actual, predicted):
        if not len(actual):
            return {
                "n": 0,
                "mae_kw": None,
                "rmse_kw": None,
                "status": "insufficient observed history",
            }
        error = np.asarray(actual) - np.asarray(predicted)
        return {
            "n": len(error),
            "mae_kw": float(np.abs(error).mean()),
            "rmse_kw": float(np.sqrt((error**2).mean())),
        }

    return {
        "cold_start": {
            **score(test.demand_kw, cold),
            "method": "training-buildings category/hour mean; held-out buildings",
        },
        "historical": {
            **score(historical.demand_kw, historical.lag_168_kw),
            "method": "previous-week same hour; final chronological 20%",
        },
        "neural_energy_dna_trained": False,
        "geographic_transfer_validated": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--meters", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument(
        "--timestamp-mode",
        choices=["utc", "local_standard", "local_wall"],
        required=True,
    )
    parser.add_argument("--meter", default="electricity")
    parser.add_argument("--unit", default="kWh")
    parser.add_argument(
        "--output", type=Path, default=Path("ml/data/generated/bdg2.parquet")
    )
    parser.add_argument(
        "--baseline-output",
        type=Path,
        default=Path("ml/artifacts/energy-dna-baseline/profiles.json"),
    )
    args = parser.parse_args()
    clean, report = prepare(
        pd.read_csv(args.meters),
        pd.read_csv(args.metadata),
        meter=args.meter,
        unit=args.unit,
        timestamp_mode=args.timestamp_mode,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    clean.to_parquet(args.output, index=False)
    report["baselines"] = evaluate_baselines(clean)
    from ml.models.energy_dna import fit_cold_start

    args.baseline_output.parent.mkdir(parents=True, exist_ok=True)
    args.baseline_output.write_text(
        json.dumps(fit_cold_start(clean), indent=2), encoding="utf8"
    )
    args.output.with_suffix(".report.json").write_text(
        json.dumps(report, indent=2), encoding="utf8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
