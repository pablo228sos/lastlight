from datetime import datetime
from math import fsum

import pytest
from hypothesis import given, settings, strategies as st

from services.simulation import engine
from services.simulation.engine import EnergyBalanceError, simulate
from services.simulation.schemas import SimulationRequest


def run(**overrides):
    return simulate(SimulationRequest.model_validate(overrides))


def assert_physics(result):
    """Independent equations checked from public output, not dispatch internals."""
    s, rows = result.input, result.trace
    b = s.battery
    assert rows
    assert rows[0].elapsed_hours == 0
    assert fsum(p.duration_hours for p in rows) == pytest.approx(
        s.duration_hours, abs=1e-10
    )
    assert len(rows) <= 2 * s.interval_count
    for p in rows:
        dt = p.duration_hours
        assert dt > 0
        assert p.t_utc.endswith("Z") and p.t_end_utc.endswith("Z")
        assert datetime.fromisoformat(p.t_utc) <= datetime.fromisoformat(p.t_end_utc)
        assert b.minimum_soc - 1e-12 <= p.battery_soc <= b.maximum_soc + 1e-12
        assert b.minimum_soc - 1e-12 <= p.battery_soc_end <= b.maximum_soc + 1e-12
        assert p.battery_energy_kwh == pytest.approx(p.battery_soc * b.capacity_kwh)
        assert p.battery_energy_end_kwh == pytest.approx(
            p.battery_soc_end * b.capacity_kwh
        )
        assert 0 <= p.battery_charge_kw <= b.max_charge_kw
        assert 0 <= p.battery_discharge_kw <= b.max_discharge_kw
        assert p.battery_charge_kw * p.battery_discharge_kw == 0
        assert (
            p.solar_kw + p.battery_discharge_kw + p.grid_charge_kw
            <= s.inverter.max_kw + 1e-9
        )
        assert 0 <= p.grid_kw <= s.grid.import_limit_kw
        assert p.grid_charge_kw <= p.battery_charge_kw
        assert p.grid_charge_kw <= p.grid_kw
        assert 0 <= p.solar_kw <= p.solar_available_kw
        assert p.solar_kw + p.solar_curtailed_kw == pytest.approx(p.solar_available_kw)
        if not p.grid_online:
            assert p.grid_kw == p.grid_charge_kw == 0
            if not (s.solar.islanding_capable and s.inverter.islanding_capable):
                assert p.solar_kw == 0
            if not s.inverter.islanding_capable:
                assert p.battery_discharge_kw == p.battery_charge_kw == 0
        if not s.grid.charge_battery:
            assert p.grid_charge_kw == 0
        assert p.critical_served_kw + p.unserved_critical_kw == pytest.approx(
            p.critical_demand_kw
        )
        assert p.noncritical_served_kw + p.unserved_noncritical_kw == pytest.approx(
            p.noncritical_demand_kw
        )
        if p.unserved_critical_kw > 1e-9:
            assert p.noncritical_served_kw == pytest.approx(0)
        # AC bus, internal storage, and total system balance, each independently.
        ac = (
            p.grid_kw
            + p.solar_kw
            + p.battery_discharge_kw
            - p.critical_served_kw
            - p.noncritical_served_kw
            - p.battery_charge_kw
        ) * dt
        delta = p.battery_energy_end_kwh - p.battery_energy_kwh
        change = (
            p.battery_charge_kw * b.charge_efficiency
            - p.battery_discharge_kw / b.discharge_efficiency
        ) * dt
        loss = (
            p.battery_charge_kw * (1 - b.charge_efficiency)
            + p.battery_discharge_kw * (1 / b.discharge_efficiency - 1)
        ) * dt
        combined = (
            (p.grid_kw + p.solar_kw - p.critical_served_kw - p.noncritical_served_kw)
            * dt
            - delta
            - loss
        )
        assert abs(ac) < 1e-8
        assert abs(delta - change) < 1e-8
        assert abs(combined) < 1e-8
        assert p.ac_balance_residual_kwh == pytest.approx(ac, abs=1e-12)
        assert p.storage_balance_residual_kwh == pytest.approx(
            delta - change, abs=1e-12
        )
        assert p.conversion_loss_kwh == pytest.approx(loss, abs=1e-12)
        assert p.balance_residual_kwh == pytest.approx(combined, abs=1e-12)
    for a, z in zip(rows, rows[1:]):
        assert a.t_end_utc == z.t_utc
        assert a.battery_energy_end_kwh == z.battery_energy_kwh
        assert a.elapsed_hours + a.duration_hours == pytest.approx(
            z.elapsed_hours, abs=1e-10
        )
    summary = result.summary
    for trace_field, summary_field in [
        ("critical_served_kw", "served_critical_kwh"),
        ("unserved_critical_kw", "unserved_critical_kwh"),
        ("noncritical_served_kw", "served_noncritical_kwh"),
        ("grid_kw", "grid_import_kwh"),
        ("solar_kw", "solar_used_kwh"),
    ]:
        assert getattr(summary, summary_field) == pytest.approx(
            fsum(getattr(p, trace_field) * p.duration_hours for p in rows)
        )
    balance = (
        summary.grid_import_kwh
        + summary.solar_used_kwh
        - summary.served_critical_kwh
        - summary.served_noncritical_kwh
        + summary.initial_battery_energy_kwh
        - summary.final_battery_energy_kwh
        - summary.conversion_loss_kwh
    )
    assert abs(balance) < 1e-8
    assert 0 <= summary.served_critical_fraction <= 1 + 1e-12
    failures = [p for p in rows if p.unserved_critical_kw > 1e-9]
    assert summary.survived_full_window == (not failures)
    assert summary.first_failure_utc == (failures[0].t_utc if failures else None)


@pytest.mark.parametrize("grid_online", [False, True])
def test_zero_grid_import_limit(grid_online):
    r = run(
        duration_hours=16,
        grid={"online": grid_online, "import_limit_kw": 0, "charge_battery": True},
        load={"noncritical_kw": 0},
    )
    assert r.summary.grid_import_kwh == 0
    assert r.summary.critical_survival_hours == pytest.approx(9.12)
    assert_physics(r)


@pytest.mark.parametrize(
    "inverter,discharge", [(1.0, 8.0), (8.0, 1.0), (0.0, 8.0), (8.0, 0.0)]
)
def test_power_bottleneck_is_immediate(inverter, discharge):
    r = run(
        inverter={"max_kw": inverter},
        battery={"max_discharge_kw": discharge},
        load={"shed_noncritical_during_outage": False},
    )
    assert r.summary.critical_survival_hours == 0
    assert r.trace[0].critical_served_kw == min(inverter, discharge)
    assert r.summary.served_noncritical_kwh == 0
    assert_physics(r)


@pytest.mark.parametrize(
    "inverter_island,pv_island,online,expected",
    [
        (False, False, False, False),
        (False, True, False, False),
        (True, False, False, False),
        (True, True, False, True),
        (False, False, True, True),
    ],
)
def test_pv_islanding_flags(inverter_island, pv_island, online, expected):
    r = run(
        duration_hours=2,
        inverter={"islanding_capable": inverter_island},
        grid={"online": online},
        solar={"generation_kw": 5, "islanding_capable": pv_island},
    )
    assert (r.summary.solar_used_kwh > 0) == expected
    if not expected:
        assert r.summary.solar_curtailed_kwh == 10
    assert_physics(r)


def test_missing_pv_data_is_zero_at_any_time():
    r = run(start_utc="2026-06-21T12:00:00Z")
    assert r.summary.solar_used_kwh == r.summary.solar_available_kwh == 0
    assert r.summary.critical_survival_hours == 9.12
    assert_physics(r)


def test_unavailable_battery_is_not_islanded_backup():
    r = run(inverter={"islanding_capable": False})
    assert r.summary.critical_survival_hours == 0
    assert r.summary.ending_soc == pytest.approx(0.8)
    assert_physics(r)


def test_solar_charge_efficiency_and_charge_limit():
    r = run(
        duration_hours=1,
        step_minutes=60,
        battery={
            "capacity_kwh": 10,
            "initial_soc": 0.2,
            "charge_efficiency": 0.8,
            "max_charge_kw": 1,
        },
        load={"critical_kw": 1, "noncritical_kw": 0},
        solar={"generation_kw": 3, "islanding_capable": True},
        inverter={"max_kw": 4},
    )
    assert r.summary.final_battery_energy_kwh == pytest.approx(2.8)
    assert r.summary.conversion_loss_kwh == pytest.approx(0.2)
    assert r.summary.solar_curtailed_kwh == pytest.approx(1)
    assert_physics(r)


def test_charge_event_splits_at_maximum_and_curtails():
    r = run(
        duration_hours=1,
        step_minutes=60,
        battery={"capacity_kwh": 10, "initial_soc": 0.9, "charge_efficiency": 0.8},
        load={"critical_kw": 1, "noncritical_kw": 0},
        solar={"generation_kw": 5, "islanding_capable": True},
    )
    assert len(r.trace) == 2
    assert r.trace[0].duration_hours == pytest.approx(0.3125)
    assert r.trace[0].battery_soc_end == 1
    assert r.trace[1].battery_charge_kw == 0
    assert r.trace[1].solar_curtailed_kw == 4
    assert_physics(r)


def test_grid_charging_respects_spare_import_and_converter_capacity():
    r = run(
        duration_hours=1,
        step_minutes=60,
        grid={"online": True, "import_limit_kw": 4, "charge_battery": True},
        load={"critical_kw": 1, "noncritical_kw": 1},
        inverter={"max_kw": 1.25},
    )
    assert r.trace[0].grid_charge_kw == 1.25
    assert r.trace[0].grid_kw == 3.25
    assert r.summary.battery_charge_kwh == 1.25
    assert_physics(r)


def test_shared_pv_and_battery_budget_prioritizes_critical():
    r = run(
        duration_hours=1,
        inverter={"max_kw": 2},
        load={
            "critical_kw": 1.5,
            "noncritical_kw": 3,
            "shed_noncritical_during_outage": False,
        },
        solar={"generation_kw": 1, "islanding_capable": True},
    )
    assert r.trace[0].critical_served_kw == 1.5
    assert r.trace[0].noncritical_served_kw == 0.5
    assert_physics(r)


def test_grid_bypasses_inverter_for_loads():
    r = run(inverter={"max_kw": 0, "islanding_capable": False}, grid={"online": True})
    assert r.summary.survived_full_window
    assert r.summary.grid_import_kwh == pytest.approx(3.5 * 12)
    assert r.summary.ending_soc == pytest.approx(0.8)
    assert all(p.status == "normal" for p in r.trace)
    assert_physics(r)


def test_outage_and_pv_profiles_with_recovery():
    r = run(
        duration_hours=1,
        step_minutes=15,
        battery={"initial_soc": 0.2},
        grid={"profile_online": [True, False, False, True]},
        solar={"profile_kw": [0, 3, 0, 0], "islanding_capable": True},
        load={"noncritical_kw": 0},
    )
    assert r.summary.critical_survival_hours == pytest.approx(
        0.5 + (1.5 * 0.25 * 0.95) * 0.95 / 1.5
    )
    assert r.trace[-1].grid_online and r.trace[-1].status == "normal"
    assert_physics(r)


@pytest.mark.parametrize("step", [1, 15, 60])
def test_exact_horizon_depletion_has_no_in_window_failure(step):
    r = run(duration_hours=9.12, step_minutes=step)
    assert r.summary.critical_survival_hours is None
    assert r.summary.unserved_critical_kwh == 0
    assert r.summary.ending_soc == pytest.approx(0.2)
    assert_physics(r)


def test_minimum_initial_soc_fails_immediately_without_energy_clamping():
    r = run(battery={"initial_soc": 0.2})
    assert r.summary.critical_survival_hours == 0
    assert r.summary.battery_discharge_kwh == 0
    assert_physics(r)


def test_zero_demand_coverage_is_defined():
    r = run(load={"critical_kw": 0, "noncritical_kw": 0})
    assert r.summary.served_critical_fraction == 1
    assert r.summary.survived_full_window
    assert r.summary.idealized_autonomy_hours is None
    assert_physics(r)


def test_noncritical_shedding_extends_critical_survival():
    shed = run()
    keep = run(load={"shed_noncritical_during_outage": False})
    assert shed.summary.critical_survival_hours > keep.summary.critical_survival_hours
    assert keep.summary.critical_survival_hours == pytest.approx(24 * 0.6 * 0.95 / 3.5)
    assert shed.trace[0].status == "degraded"
    assert_physics(shed)
    assert_physics(keep)


@pytest.mark.parametrize(
    "capacity,soc,eta,critical",
    [
        (7.3, 0.63, 0.82, 0.713),
        (0.001, 0.8, 0.01, 50_000),
        (123.45, 0.933, 0.977, 31.7),
    ],
)
def test_other_failures_are_derived_from_constraints(capacity, soc, eta, critical):
    r = run(
        duration_hours=48,
        step_minutes=17,
        battery={
            "capacity_kwh": capacity,
            "initial_soc": soc,
            "discharge_efficiency": eta,
            "max_discharge_kw": 50_000,
        },
        load={"critical_kw": critical},
        inverter={"max_kw": 50_000},
    )
    expected = capacity * (soc - 0.2) * eta / critical
    assert r.summary.critical_survival_hours == pytest.approx(expected, abs=1e-10)
    assert_physics(r)


@settings(max_examples=100, deadline=None, derandomize=True)
@given(
    capacity=st.floats(min_value=1, max_value=1000),
    initial=st.floats(min_value=0.2, max_value=1),
    critical=st.floats(min_value=0, max_value=30),
    noncritical=st.floats(min_value=0, max_value=30),
    pv=st.lists(st.floats(min_value=0, max_value=50), min_size=8, max_size=8),
    online=st.lists(st.booleans(), min_size=8, max_size=8),
    inverter=st.floats(min_value=0, max_value=40),
    eta=st.floats(min_value=0.1, max_value=1),
    charge=st.floats(min_value=0, max_value=40),
    discharge=st.floats(min_value=0, max_value=40),
    island=st.booleans(),
    pv_island=st.booleans(),
    shed=st.booleans(),
    grid_charge=st.booleans(),
)
def test_randomized_energy_and_equipment_invariants(
    capacity,
    initial,
    critical,
    noncritical,
    pv,
    online,
    inverter,
    eta,
    charge,
    discharge,
    island,
    pv_island,
    shed,
    grid_charge,
):
    r = run(
        duration_hours=2,
        step_minutes=15,
        battery={
            "capacity_kwh": capacity,
            "initial_soc": initial,
            "charge_efficiency": eta,
            "discharge_efficiency": eta,
            "max_charge_kw": charge,
            "max_discharge_kw": discharge,
        },
        inverter={"max_kw": inverter, "islanding_capable": island},
        load={
            "critical_kw": critical,
            "noncritical_kw": noncritical,
            "shed_noncritical_during_outage": shed,
        },
        solar={"profile_kw": pv, "islanding_capable": pv_island},
        grid={
            "profile_online": online,
            "charge_battery": grid_charge,
            "import_limit_kw": 10,
        },
    )
    assert_physics(r)


@settings(max_examples=40, deadline=None, derandomize=True)
@given(
    capacity=st.floats(min_value=1, max_value=100),
    extra=st.floats(min_value=0, max_value=100),
)
def test_capacity_monotonicity(capacity, extra):
    a = run(duration_hours=48, battery={"capacity_kwh": capacity})
    z = run(duration_hours=48, battery={"capacity_kwh": capacity + extra})
    assert z.summary.served_critical_kwh >= a.summary.served_critical_kwh - 1e-9
    assert z.summary.unserved_critical_kwh <= a.summary.unserved_critical_kwh + 1e-9


@pytest.mark.parametrize(
    "field,low,high",
    [
        ("initial_soc", 0.5, 0.9),
        ("discharge_efficiency", 0.7, 0.98),
        ("max_discharge_kw", 0.9, 2.0),
    ],
)
def test_battery_upgrade_monotonicity(field, low, high):
    a, z = run(battery={field: low}), run(battery={field: high})
    assert z.summary.served_critical_kwh >= a.summary.served_critical_kwh
    assert z.summary.unserved_critical_kwh <= a.summary.unserved_critical_kwh


def test_energy_audit_rejects_artificial_source_energy(monkeypatch):
    def inconsistent_dispatch(*_args):
        return engine.Dispatch(
            grid=1,
            solar=0,
            charge=0,
            discharge=0,
            grid_charge=0,
            critical=0,
            noncritical=0,
        )

    monkeypatch.setattr(engine, "dispatch", inconsistent_dispatch)
    with pytest.raises(EnergyBalanceError, match="energy conservation"):
        run()


def test_partial_final_interval_and_profile_override():
    r = run(
        duration_hours=1.1,
        step_minutes=60,
        load={"noncritical_kw": 0},
        grid={"online": False, "profile_online": [True, True]},
        solar={"generation_kw": 99, "profile_kw": [0, 0]},
    )
    assert len(r.trace) == 2
    assert r.trace[-1].duration_hours == pytest.approx(0.1)
    assert r.summary.solar_available_kwh == 0
    assert r.summary.grid_import_kwh == pytest.approx(1.65)
    assert_physics(r)


def test_maximum_horizon_at_finest_sampling():
    r = run(
        duration_hours=168, step_minutes=1, load={"critical_kw": 0, "noncritical_kw": 0}
    )
    assert len(r.trace) == 10_080
    assert r.trace[-1].t_end_utc == "2026-01-08T00:00:00Z"
    assert r.summary.survived_full_window
    assert_physics(r)
