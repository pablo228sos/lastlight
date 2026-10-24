import numpy as np
import pandas as pd
import pytest

from ml.data.prepare_bdg2 import prepare, evaluate_baselines
from ml.models.energy_dna import forecast_historical


def test_meter_units_missing_time_alignment_and_group_splits():
    stamps = pd.date_range("2016-01-01", periods=400, freq="h")
    meters = pd.DataFrame(
        {"timestamp": stamps, **{f"b{i}": np.ones(400) * i for i in range(1, 7)}}
    )
    meters.loc[5, "b1"] = np.nan
    metadata = pd.DataFrame(
        {
            "building_id": [f"b{i}" for i in range(1, 7)],
            "timezone": ["America/New_York"] * 6,
            "primaryspaceusage": ["Education"] * 6,
        }
    )
    clean, report = prepare(
        meters,
        metadata,
        meter="electricity",
        unit="kWh",
        timestamp_mode="local_standard",
    )
    assert report["missing_readings"] == 1
    assert clean[clean.building_id == "b1"].demand_kw.isna().sum() == 1
    assert str(clean.timestamp_utc.dt.tz) == "UTC"
    assert clean.timestamp_utc.min().hour == 5
    assert clean.groupby("building_id").split.nunique().max() == 1
    assert "lag_168_kw" in clean
    scores = evaluate_baselines(clean)
    assert scores["historical"]["mae_kw"] == pytest.approx(0)
    with pytest.raises(ValueError):
        prepare(meters, metadata, meter="water", unit="kWh", timestamp_mode="utc")
    with pytest.raises(ValueError):
        prepare(
            meters, metadata, meter="electricity", unit="kW", timestamp_mode="guess"
        )
    assert forecast_historical([2] * 168, 24) == [2] * 24
    with pytest.raises(ValueError):
        forecast_historical([2] * 167)
