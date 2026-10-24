"""EnergyDNA preparation baselines. No neural demand model is claimed."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

BASELINE_VERSION = "energy-dna-baselines-1"


def fit_cold_start(clean):
    training = clean[clean.split == "train"].dropna(subset=["demand_kw"])
    if training.empty:
        raise ValueError("No observed training-building values")
    category = training.groupby(["primaryspaceusage", "hour_local"]).demand_kw.mean()
    global_profile = training.groupby("hour_local").demand_kw.mean()
    return {
        "model_version": BASELINE_VERSION,
        "training_buildings": sorted(training.building_id.unique().tolist()),
        "global_hourly_kw": {
            str(hour): float(value) for hour, value in global_profile.items()
        },
        "category_hourly_kw": {
            f"{group}|{hour}": float(value) for (group, hour), value in category.items()
        },
        "fallback_kw": float(training.demand_kw.mean()),
        "units": "whole-building average kW",
        "provenance": "Research-derived from BDG2 overseas training buildings; not Kyrgyzstan measurements.",
    }


def forecast_historical(history_kw, hours=24):
    values = np.asarray(history_kw, dtype=float)
    if (
        values.ndim != 1
        or len(values) < 168
        or not np.isfinite(values).all()
        or (values < 0).any()
        or not 1 <= hours <= 24
    ):
        raise ValueError(
            "Historical mode needs >=168 contiguous observed hourly nonnegative kW values"
        )
    return values[-168 : -168 + hours if hours < 168 else None].tolist()


def forecast_cold_start(
    profile, category, start_utc: datetime, local_timezone="UTC", hours=24
):
    if start_utc.utcoffset() is None or not 1 <= hours <= 24:
        raise ValueError("Timezone-aware forecast start and 1..24 hours required")
    zone = ZoneInfo(local_timezone)
    return [
        profile["category_hourly_kw"].get(
            f"{category}|{(start_utc + timedelta(hours=i)).astimezone(zone).hour}",
            profile["global_hourly_kw"].get(
                str((start_utc + timedelta(hours=i)).astimezone(zone).hour),
                profile["fallback_kw"],
            ),
        )
        for i in range(hours)
    ]
