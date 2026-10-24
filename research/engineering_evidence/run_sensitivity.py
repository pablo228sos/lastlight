"""Research-only experiment using an unchanged, hash-pinned official engine.

Run with the Python 3.12 environment installed by the official service launcher.
No simulation equation is reimplemented; the formula below is an independent
constant-load cross-check of results returned by services.simulation.engine.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIN_PATH = Path(__file__).with_name("engine_pin.json")
FIELDS = [
    "case_id",
    "role",
    "capacity_kwh",
    "initial_soc",
    "minimum_soc",
    "critical_load_kw",
    "solar_kw",
    "discharge_efficiency",
    "horizon_hours",
    "step_minutes",
    "observed_first_failure_hours",
    "first_failure_utc",
    "survived_full_window",
    "unserved_critical_kwh",
    "ending_soc",
    "independent_analytic_autonomy_hours",
    "max_balance_residual_kwh",
    "model_version",
    "schema_version",
    "seed",
    "input_hash",
    "run_id",
    "input_json",
    "reproduction_command_posix",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configurations():
    for capacity in [24, 36]:
        for soc in [0.4, 0.8]:
            for load in [0.75, 1.5, 3.0]:
                for horizon in [12, 32]:
                    for step in [15, 1, 60]:
                        name = f"c{capacity}-soc{int(soc * 100)}-p{load:g}-h{horizon}-m{step}"
                        body = {
                            "battery": {"capacity_kwh": capacity, "initial_soc": soc},
                            "load": {"critical_kw": load},
                            "duration_hours": horizon,
                            "step_minutes": step,
                            "provenance": {
                                "category": "synthetic",
                                "references": [
                                    "docs/physics/MODEL.md",
                                    "docs/research/SENSITIVITY_STUDY.md",
                                ],
                            },
                        }
                        yield name, "study" if step == 15 else "time_step_check", body
    for step in [1, 15, 60]:
        yield (
            f"exclusive-horizon-m{step}",
            "boundary_check",
            {
                "duration_hours": 9.12,
                "step_minutes": step,
                "provenance": {
                    "category": "synthetic",
                    "references": ["docs/research/SENSITIVITY_STUDY.md"],
                },
            },
        )


def cross_check(result) -> float:
    request, summary = result.input, result.summary
    b, load, horizon = request.battery, request.load.critical_kw, request.duration_hours
    analytic = (
        b.capacity_kwh * (b.initial_soc - b.minimum_soc) * b.discharge_efficiency / load
    )
    # Independent analytic result is never used as the reported observed event.
    expected_failure = analytic if horizon > analytic + 1e-10 else None
    if expected_failure is None:
        assert (
            summary.first_failure_utc is None
            and summary.critical_survival_hours is None
        )
    else:
        assert math.isclose(
            summary.critical_survival_hours, expected_failure, abs_tol=1e-9
        )
        expected_stamp = request.start_utc + timedelta(hours=expected_failure)
        actual_stamp = datetime.fromisoformat(
            summary.first_failure_utc.replace("Z", "+00:00")
        )
        assert abs((actual_stamp - expected_stamp).total_seconds()) < 1e-5
    assert summary.survived_full_window == (expected_failure is None)
    available_ac = (
        b.capacity_kwh * (b.initial_soc - b.minimum_soc) * b.discharge_efficiency
    )
    assert math.isclose(
        summary.unserved_critical_kwh,
        max(0, load * horizon - available_ac),
        abs_tol=1e-9,
    )
    assert math.isclose(
        summary.ending_soc,
        max(
            b.minimum_soc,
            b.initial_soc - load * horizon / (b.capacity_kwh * b.discharge_efficiency),
        ),
        abs_tol=1e-10,
    )
    assert summary.max_balance_residual_kwh < 1e-8
    assert abs(summary.cumulative_balance_residual_kwh) < 1e-8
    assert math.isclose(
        math.fsum(p.duration_hours for p in result.trace), horizon, abs_tol=1e-10
    )
    for p in result.trace:
        assert p.grid_kw == p.solar_kw == p.battery_charge_kw == 0
        assert (
            p.duration_hours > 0
            and b.minimum_soc - 1e-12 <= p.battery_soc_end <= b.maximum_soc + 1e-12
        )
        loss = (
            p.battery_discharge_kw * (1 / b.discharge_efficiency - 1) * p.duration_hours
        )
        residual = (
            -(p.critical_served_kw + p.noncritical_served_kw) * p.duration_hours
            - (p.battery_energy_end_kwh - p.battery_energy_kwh)
            - loss
        )
        assert abs(residual) < 1e-8
    return analytic


def number(value) -> str:
    return "null" if value is None else format(value, ".12g")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine-root", type=Path, required=True)
    parser.add_argument(
        "--case-id", help="Emit one full engine result as JSON, without changing files"
    )
    parser.add_argument(
        "--check", action="store_true", help="Recompute and fail on CSV/manifest drift"
    )
    args = parser.parse_args()
    pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    engine_root = args.engine_root.resolve()
    for name, expected in pin["source_sha256"].items():
        if not (engine_root / name).is_file() or digest(engine_root / name) != expected:
            parser.error(
                f"Official engine pin mismatch: {name}; use commit {pin['commit']}"
            )
    if sys.version_info[:2] != (3, 12):
        parser.error("Use the official Python 3.12 locked runtime")
    if importlib.metadata.version("pydantic") != pin["pydantic_version"]:
        parser.error(
            "Use the official hash-locked service environment (Pydantic version mismatch)"
        )
    sys.path.insert(0, str(engine_root))
    from services.simulation.engine import simulate
    from services.simulation.schemas import SimulationRequest

    selected = list(configurations())
    if args.case_id:
        selected = [item for item in selected if item[0] == args.case_id]
        if not selected:
            parser.error("Unknown case ID")
    rows = []
    for name, role, body in selected:
        result = simulate(SimulationRequest.model_validate(body))
        analytic = cross_check(result)
        assert (
            result.model_version == pin["model_version"]
            and result.schema_version == pin["schema_version"]
        )
        if args.case_id:
            print(result.model_dump_json(indent=2))
            return
        request, summary = result.input, result.summary
        row = dict(
            zip(
                FIELDS,
                [
                    name,
                    role,
                    number(request.battery.capacity_kwh),
                    number(request.battery.initial_soc),
                    number(request.battery.minimum_soc),
                    number(request.load.critical_kw),
                    number(request.solar.generation_kw),
                    number(request.battery.discharge_efficiency),
                    number(request.duration_hours),
                    request.step_minutes,
                    number(summary.critical_survival_hours),
                    summary.first_failure_utc or "null",
                    str(summary.survived_full_window).lower(),
                    number(summary.unserved_critical_kwh),
                    number(summary.ending_soc),
                    number(analytic),
                    number(summary.max_balance_residual_kwh),
                    result.model_version,
                    result.schema_version,
                    result.seed,
                    result.input_hash,
                    result.run_id,
                    json.dumps(
                        request.model_dump(mode="json"),
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    "../lastlight-physics/services/simulation/.venv/bin/python research/engineering_evidence/run_sensitivity.py --engine-root ../lastlight-physics --case-id "
                    + name,
                ],
            )
        )
        rows.append(row)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    csv_content = buffer.getvalue()
    study = [r for r in rows if r["role"] == "study"]
    survives_12 = sum(
        r["survived_full_window"] == "true" for r in study if r["horizon_hours"] == "12"
    )
    manifest = {
        "data_category": "synthetic_scenario_results",
        "engine_pin": pin,
        "report_precision": "12 significant digits; exact resolved inputs in input_json; full trace via --case-id",
        "unique_engine_results": len(rows),
        "study_rows": len(study),
        "time_step_checks": sum(r["role"] == "time_step_check" for r in rows),
        "exclusive_horizon_checks": sum(r["role"] == "boundary_check" for r in rows),
        "all_analytic_cross_checks_passed": True,
        "surviving_12h_configurations": survives_12,
        "configurations_per_horizon": 12,
        "largest_observed_autonomy_hours": max(
            float(r["observed_first_failure_hours"])
            for r in study
            if r["horizon_hours"] == "32"
        ),
        "csv_sha256": hashlib.sha256(csv_content.encode()).hexdigest(),
        "remarks": [
            "Observed events come exclusively from the official engine.",
            "A null event is censored at the horizon, not infinite autonomy.",
            "Sampling checks are repeated input assumptions, not independent field trials.",
            "The fraction of design points surviving is not an outage probability.",
        ],
    }
    out = ROOT / "docs/research/data"
    artifacts = {
        "sensitivity_results.csv": csv_content,
        "sensitivity_manifest.json": json.dumps(manifest, indent=2) + "\n",
    }
    for name, content in artifacts.items():
        path = out / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit("Research result drift: " + name)
        else:
            out.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    print(
        f"{'Verified' if args.check else 'Generated'} {len(rows)} engine results; {survives_12}/12 design points survive 12 h; all cross-checks pass"
    )


if __name__ == "__main__":
    main()
