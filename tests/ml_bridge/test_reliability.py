import numpy as np
import pytest

from research.reliability.features import timing_features, NAMES
from services.simulation.schemas import SimulationRequest


def test_timing_features_use_inputs_and_preserve_order():
    early = SimulationRequest.model_validate(
        {
            "duration_hours": 4,
            "step_minutes": 60,
            "grid": {"profile_online": [False, False, True, True]},
        }
    )
    late = SimulationRequest.model_validate(
        {
            "duration_hours": 4,
            "step_minutes": 60,
            "grid": {"profile_online": [True, True, False, False]},
        }
    )
    a, b = timing_features(early), timing_features(late)
    assert a[NAMES.index("first_restoration_hours")] == 2
    assert b[NAMES.index("first_restoration_hours")] == 0
    assert not np.array_equal(a, b)
    assert a[NAMES.index("initial_useful_ac_kwh")] == pytest.approx(13.68)


def test_temporal_features_do_not_import_or_call_simulator():
    import inspect
    from research.reliability import features

    assert "services.simulation.engine" not in inspect.getsource(features)
    assert len(timing_features(SimulationRequest())) == len(NAMES)
