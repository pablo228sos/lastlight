from dataclasses import replace
from math import isclose
import pytest
from backend.simulation import Scenario,run

BASE = Scenario(duration_hours=16,sky_condition='no_solar',pv_peak_kw=0)

def test_known_case_baseline():
    r=run(BASE)
    assert isclose(r['summary']['first_failure_hours'],9.12,abs_tol=1e-4)
    assert isclose(r['summary']['unserved_critical_energy_kwh'],(16-9.12)*1.5,abs_tol=1e-6)
    assert isclose(r['summary']['ending_soc_pct'],20,abs_tol=1e-6)

def test_known_case_upgrade():
    r=run(replace(BASE,capacity_kwh=36))
    assert isclose(r['summary']['first_failure_hours'],13.68,abs_tol=1e-4)

def test_known_case_precharge():
    r=run(replace(BASE,initial_soc=100))
    assert isclose(r['summary']['first_failure_hours'],12.16,abs_tol=1e-4)

def test_night_pv_stays_zero():
    r=run(replace(BASE,pv_peak_kw=99,sky_condition='no_solar'))
    assert r['summary']['pv_generated_kwh']==0

def test_islanding_required_for_pv():
    r=run(replace(BASE,sky_condition='winter_clear',start_hour=9,pv_peak_kw=12,islanding_capable=False))
    assert r['summary']['pv_generated_kwh']==0

def test_solar_can_charge_battery():
    s=replace(BASE,duration_hours=6,start_hour=10,sky_condition='winter_clear',pv_peak_kw=12,initial_soc=50)
    r=run(s)
    assert r['summary']['pv_used_kwh']>0
    assert r['summary']['ending_soc_pct']>50

def test_power_limited_failure_is_immediate():
    r=run(replace(BASE,max_discharge_kw=1.0))
    assert r['summary']['first_failure_hours']==0

def test_shed_noncritical_helps():
    a=run(replace(BASE,shed_noncritical=True))
    b=run(replace(BASE,shed_noncritical=False))
    assert a['summary']['unserved_critical_energy_kwh'] <= b['summary']['unserved_critical_energy_kwh']

def test_conservation_and_monotonic_no_pv():
    r=run(BASE)
    trace=r['trace']
    for before, after in zip(trace,trace[1:]):
        assert after['soc_pct']<=before['soc_pct']+1e-6
        assert after['soc_pct']>=20-1e-6
        assert after['critical_served_kw']+after['unserved_critical_kw']==pytest.approx(1.5)
        assert after['battery_discharge_kw'] <= 8

def test_bad_soc_rejected():
    with pytest.raises(ValueError): run(replace(BASE,minimum_soc=95,initial_soc=70))

def test_same_input_same_results():
    assert run(BASE)==run(BASE)
