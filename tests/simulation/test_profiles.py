from copy import deepcopy
import random

import pytest
from pydantic import ValidationError

from services.simulation.engine import simulate
from services.simulation.schemas import SimulationRequest


def test_variable_load_profiles_and_exact_depletion():
    scenario = SimulationRequest.model_validate({
        'duration_hours': 1,
        'battery': {'capacity_kwh': 1, 'initial_soc': 1, 'minimum_soc': 0,
                    'discharge_efficiency': 1},
        'load': {'critical_profile_kw': [1, 1, 2, 2], 'noncritical_profile_kw': [0, 0, 0, 0]},
    })
    result = simulate(scenario)
    assert result.summary.critical_survival_hours == pytest.approx(.75)
    assert result.summary.total_critical_demand_kwh == pytest.approx(1.5)
    assert result.summary.unserved_critical_kwh == pytest.approx(.5)
    assert result.trace[0].critical_served_kw == 1
    assert result.physics_version and result.assumptions


def test_zero_source_starts_failed_without_dummy_point():
    result = simulate(SimulationRequest.model_validate({'inverter': {'max_kw': 0}}))
    assert result.summary.critical_survival_hours == 0
    assert result.trace[0].critical_served_kw == 0
    assert all(p.duration_hours > 0 for p in result.trace)


@pytest.mark.parametrize('body', [
    {'battery': {'initial_soc': '0.8'}}, {'inverter': {'islanding_capable': 'false'}},
    {'solar': {'profile_kw': [1]}}, {'load': {'critical_profile_kw': [1]}},
    {'load': {'critical_profile_kw': [float('nan')] * 48}},
    {'battery': {'minimum_soc': .9, 'initial_soc': .8}}, {'unknown': 1},
])
def test_bad_parameters_rejected(body):
    with pytest.raises(ValidationError):
        SimulationRequest.model_validate(body)


def test_solar_charge_bounds_islanding_and_priority():
    body = {'duration_hours': 1, 'battery': {'initial_soc': .9, 'maximum_soc': .9},
            'solar': {'profile_kw': [8, 8, 0, 0], 'islanding_capable': True},
            'load': {'critical_profile_kw': [1, 2, 3, 4], 'noncritical_kw': 4,
                     'shed_noncritical_during_outage': False}}
    result = simulate(SimulationRequest.model_validate(body))
    assert all(p.battery_soc_end <= .9 for p in result.trace)
    assert all(p.critical_served_kw == p.critical_demand_kw for p in result.trace)
    body['inverter'] = {'islanding_capable': False}
    blocked = simulate(SimulationRequest.model_validate(body))
    assert blocked.summary.solar_used_kwh == 0
    assert blocked.summary.served_critical_fraction == 0


def test_seeded_variable_profiles_conserve_energy():
    rng = random.Random(20261024)
    for _ in range(100):
        body = {'duration_hours': 2, 'battery': {'capacity_kwh': rng.uniform(.1, 30)},
                'solar': {'profile_kw': [rng.uniform(0, 20) for _ in range(8)], 'islanding_capable': True},
                'load': {'critical_profile_kw': [rng.uniform(0, 8) for _ in range(8)],
                         'noncritical_profile_kw': [rng.uniform(0, 8) for _ in range(8)],
                         'shed_noncritical_during_outage': False}}
        request = SimulationRequest.model_validate(body)
        result = simulate(request)
        assert result == simulate(deepcopy(request))
        assert result.summary.max_balance_residual_kwh < 1e-8
        assert abs(result.summary.cumulative_balance_residual_kwh) < 1e-8
        for p in result.trace:
            assert .2 <= p.battery_soc_end <= 1
            assert p.solar_kw + p.battery_discharge_kw <= 8 + 1e-8
            assert p.grid_kw == 0
            assert min(p.battery_charge_kw, p.battery_discharge_kw) == 0
