"""Research selection only; every returned candidate gets its own official run."""

from services.simulation.engine import simulate
from services.simulation.frontier import scenario_at
from .adapter import DEFAULT_CHECKPOINT, analyze_neural, predictor
from .contracts import CandidateRequest, CandidateResult, VerifiedCandidate
from .features import features
from .runtime import source_identity


def suggest(request: CandidateRequest, checkpoint_dir=DEFAULT_CHECKPOINT):
    request = CandidateRequest.model_validate(request.model_dump())
    identity = source_identity()
    availability = analyze_neural(request.scenario, checkpoint_dir)
    warnings = [
        *availability.warnings,
        "Research test selection has no demonstrated Frontier speed advantage. Candidate counts are not accuracy or measured events.",
    ]
    if availability.status != "available":
        return CandidateResult(
            neural_status=availability.status,
            neural_model_version=None,
            candidates=[],
            warnings=warnings,
        )
    model = predictor(checkpoint_dir.resolve(), identity["source_sha256"])
    scenarios = [
        scenario_at(request.scenario, point.initial_soc, point.duration_hours)
        for point in request.points
    ]
    scores = model.scores([features(scenario) for scenario in scenarios])
    chosen = sorted(
        range(len(scores)),
        key=lambda i: (abs(float(scores[i]) - model.manifest["threshold"]), i),
    )[: request.limit]
    candidates = []
    for index in chosen:
        physics = simulate(scenarios[index])
        estimate, notices = model.predict(scenarios[index])
        candidates.append(
            VerifiedCandidate(
                **request.points[index].model_dump(),
                neural=estimate,
                physics_run_id=physics.run_id,
                input_hash=physics.input_hash,
                physics_summary=physics.summary,
                warnings=notices,
            )
        )
    return CandidateResult(
        neural_status="available",
        neural_model_version=availability.model_version,
        candidates=candidates,
        warnings=warnings,
    )
