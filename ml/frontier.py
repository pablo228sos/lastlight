"""Physics reference maps and explicitly unverified ML boundary proposals."""

import hashlib
import json
from pathlib import Path
from time import perf_counter
from uuid import uuid5, NAMESPACE_URL
from typing import TYPE_CHECKING

import numpy as np

from ml.features import features

if TYPE_CHECKING:
    from ml.models.fragility_net import FragilityPredictor
from services.simulation import MODEL_VERSION
from services.simulation.engine import simulate
from services.simulation.schemas import SimulationRequest

DEFAULT_MODEL = Path(__file__).parent / "artifacts" / "fragility-v1"


def scenario_at(s: SimulationRequest, soc: float, hours: float) -> SimulationRequest:
    body = s.model_dump(mode="json")
    body["battery"]["initial_soc"] = float(soc)
    body["duration_hours"] = float(hours)
    count = int(np.ceil(hours * 60 / s.step_minutes))
    for owner, field in [
        ("load", "critical_profile_kw"),
        ("load", "noncritical_profile_kw"),
        ("solar", "profile_kw"),
        ("grid", "profile_online"),
    ]:
        profile = body[owner][field]
        if profile is not None:
            if count > len(profile):
                raise ValueError("Frontier cannot extrapolate a supplied time profile")
            body[owner][field] = profile[:count]
    return SimulationRequest.model_validate(body)


def axes(s, soc_points, duration_points, maximum_hours):
    if not (
        3 <= soc_points <= 41
        and 3 <= duration_points <= 49
        and soc_points * duration_points <= 1600
    ):
        raise ValueError("Frontier dimensions exceed bounded computation budget")
    if not 0.25 <= maximum_hours <= 48:
        raise ValueError("maximum_hours must be .25..48")
    socs = np.linspace(s.battery.minimum_soc, s.battery.maximum_soc, soc_points)
    hours = np.linspace(0.25, maximum_hours, duration_points)
    return socs, hours


def physics_frontier(
    s: SimulationRequest,
    soc_points=13,
    duration_points=21,
    maximum_hours=24,
    predictor: "FragilityPredictor | None" = None,
) -> dict:
    socs, hours = axes(s, soc_points, duration_points, maximum_hours)
    cells = []
    for soc in socs:
        result = simulate(scenario_at(s, soc, maximum_hours))
        failure = result.summary.critical_survival_hours
        # Each shorter horizon is a prefix of the same deterministic trace.
        for horizon in hours:
            cells.append(
                {
                    "initial_soc": float(soc),
                    "duration_hours": float(horizon),
                    "failed": failure is not None and float(horizon) > failure + 1e-10,
                    "first_failure_hours": failure
                    if failure is not None and float(horizon) > failure + 1e-10
                    else None,
                    "physics_verified": True,
                    "verification_run_id": result.run_id,
                }
            )
    estimates, verified = [], []
    if predictor is not None:
        requests = [
            scenario_at(s, c["initial_soc"], c["duration_hours"]) for c in cells
        ]
        matrix = np.stack([features(r) for r in requests])
        scores = predictor.scores(matrix)
        outside = np.any(
            (matrix < np.asarray(predictor.metadata["domain_min"]) - 1e-6)
            | (matrix > np.asarray(predictor.metadata["domain_max"]) + 1e-6),
            axis=1,
        )
        estimates = [
            {
                "initial_soc": c["initial_soc"],
                "duration_hours": c["duration_hours"],
                "synthetic_failure_score": float(score),
                "physics_verified": False,
                "outside_training_domain": bool(ood),
            }
            for c, score, ood in zip(cells, scores, outside)
        ]
        for index in np.argsort(
            np.abs(scores - predictor.metadata["threshold"]), kind="stable"
        )[: min(12, len(cells))]:
            result = simulate(requests[int(index)])
            verified.append(
                {
                    **estimates[int(index)],
                    "physics_verified": True,
                    "failed": not result.summary.survived_full_window,
                    "run_id": result.run_id,
                }
            )
    identity = {
        "input": s.model_dump(mode="json"),
        "soc_points": soc_points,
        "duration_points": duration_points,
        "maximum_hours": maximum_hours,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "run_id": str(uuid5(NAMESPACE_URL, f"frontier:{MODEL_VERSION}:{digest}")),
        "physics_version": MODEL_VERSION,
        "model_version": predictor.metadata["model_version"] if predictor else None,
        "input_hash": digest,
        "seed": s.seed,
        "assumptions": [
            "SOC fractions; outage horizon hours; fixed equipment and input-profile prefix.",
            "ML scores are proposals conditional on synthetic data, not engineering clearance.",
            "Out-of-domain proposals are marked and cannot override physics.",
        ],
        "provenance": s.provenance.model_dump(),
        "summary": {
            "physics_calls": soc_points + len(verified),
            "verified_cells": len(cells),
            "method": "one full physics trace per SOC column; selected ML candidates re-simulated",
        },
        "trace": cells,
        "ml_estimates": estimates,
        "verified_candidates": verified,
        "warnings": []
        if predictor is not None
        else ["No ML model used; this map is calculated by physics."],
    }


def benchmark(
    s: SimulationRequest,
    predictor: "FragilityPredictor",
    soc_points=17,
    duration_points=33,
    maximum_hours=24,
    budget=80,
    seed=20261024,
) -> dict:
    socs, hours = axes(s, soc_points, duration_points, maximum_hours)
    points = np.array([(soc, h) for soc in socs for h in hours])
    requests = [scenario_at(s, soc, h) for soc, h in points]
    start = perf_counter()
    truth = np.array([not simulate(r).summary.survived_full_window for r in requests])
    reference_seconds = perf_counter() - start
    budget = min(budget, len(points))
    scaled = (points - points.min(axis=0)) / np.maximum(np.ptp(points, axis=0), 1e-9)
    rng = np.random.default_rng(seed)
    records = {}

    def quality(predicted):
        def boundary(labels):
            grid = labels.reshape(soc_points, duration_points)
            return np.array(
                [
                    hours[np.where(row)[0][0]] if row.any() else maximum_hours
                    for row in grid
                ]
            )

        return {
            "mean_boundary_error_hours": float(
                np.mean(np.abs(boundary(predicted) - boundary(truth)))
            ),
            "missed_unsafe_cells": int(np.sum(truth & ~predicted)),
            "classification_error": float(np.mean(predicted != truth)),
        }

    for method in ["uniform", "random", "ml_guided"]:
        start = perf_counter()
        if method == "uniform":
            indices = np.linspace(0, len(points) - 1, budget, dtype=int)
        elif method == "random":
            indices = rng.choice(len(points), budget, replace=False)
        else:
            scores = predictor.scores(np.stack([features(r) for r in requests]))
            distance = np.abs(scores - predictor.metadata["threshold"])
            # Cover every SOC column, then spend remaining calls near the learned boundary.
            anchors = []
            for column in range(soc_points):
                start_index = column * duration_points
                anchors.extend(
                    [
                        start_index,
                        start_index + duration_points - 1,
                        start_index
                        + int(
                            distance[
                                start_index : start_index + duration_points
                            ].argmin()
                        ),
                    ]
                )
            ordered = list(
                dict.fromkeys(anchors + np.argsort(distance, kind="stable").tolist())
            )
            indices = np.asarray(ordered[:budget])
        labels = np.array(
            [
                not simulate(requests[int(i)]).summary.survived_full_window
                for i in indices
            ]
        )
        nearest = (
            ((scaled[:, None, :] - scaled[indices][None, :, :]) ** 2)
            .sum(axis=2)
            .argmin(axis=1)
        )
        predicted = labels[nearest]
        records[method] = {
            "physics_calls": int(len(indices)),
            "seconds": perf_counter() - start,
            **quality(predicted),
        }
    start = perf_counter()
    direct = physics_frontier(s, soc_points, duration_points, maximum_hours)
    predicted = np.array([c["failed"] for c in direct["trace"]])
    records["deterministic_trace"] = {
        "physics_calls": soc_points,
        "seconds": perf_counter() - start,
        **quality(predicted),
    }
    return {
        "physics_version": MODEL_VERSION,
        "model_version": predictor.metadata["model_version"],
        "seed": seed,
        "grid": [soc_points, duration_points],
        "reference": {"physics_calls": len(points), "seconds": reference_seconds},
        "methods": records,
        "claim": "Compare measured calls, planning-inclusive times and errors; no ML acceleration assumed.",
    }
