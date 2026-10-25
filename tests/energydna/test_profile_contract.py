from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from research.energydna.profile_contract import (
    ForecastSeries,
    allocate_research,
    to_official_v1,
)


def sample(**changes):
    body = dict(
        source_building_id="research-building",
        source_references=["reviewed source"],
        source_sha256="a" * 64,
        model_version="research-only",
        forecast_origin=datetime(2016, 3, 20, tzinfo=timezone.utc),
        source_timezone="UTC",
        horizon_hours=2,
        whole_building_kw=[2.0, 4.0],
        missing_data_policy="no imputed targets; causal history",
        critical_fraction=0.25,
        allocation_evidence="separate circuit audit required",
        allocation_reviewer="research reviewer",
    )
    return ForecastSeries(**{**body, **changes})


def test_research_allocation_conserves_units_and_refuses_official_v1_injection():
    source = sample()
    result = allocate_research(source)
    assert result["critical_kw"] == [0.5, 1.0]
    assert result["noncritical_kw"] == [1.5, 3.0]
    assert result["total_energy_kwh"] == 6.0
    assert result["official_v1_dynamic_load_compatible"] is False
    with pytest.raises(ValueError, match="1.0.0"):
        to_official_v1(source)


@pytest.mark.parametrize(
    "changes",
    [
        {"forecast_origin": datetime(2016, 3, 20)},
        {"whole_building_kw": [float("nan"), 1.0]},
        {"whole_building_kw": [2.0]},
        {"critical_fraction": 1.1},
        {"source_timezone": "not/a/timezone"},
        {"lower_kw": [1.0, 2.0]},
        {"lower_kw": [3.0, 2.0], "upper_kw": [4.0, 5.0]},
    ],
)
def test_invalid_or_unresolved_forecast_is_rejected(changes):
    with pytest.raises(ValidationError):
        sample(**changes)
