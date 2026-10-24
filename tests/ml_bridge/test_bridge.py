from pathlib import Path

import pytest
from pydantic import ValidationError

from ml_bridge.adapter import assess
from ml_bridge.contracts import AssessmentRequest
from services.simulation.engine import simulate
from services.simulation.schemas import SimulationRequest
from ml_bridge.features import feature_source_sha256
from ml_bridge.runtime import source_identity
import services.simulation.engine as official_engine


def test_feature_source_contract_has_a_stable_serializable_fingerprint():
    value = feature_source_sha256()
    assert len(value) == 64
    assert int(value, 16) >= 0
    assert feature_source_sha256() == value


def test_runtime_fingerprint_follows_the_actually_imported_engine(
    monkeypatch, tmp_path
):
    before = source_identity()["source_sha256"]
    changed_source = tmp_path / "engine.py"
    changed_source.write_text(
        Path(official_engine.__file__).read_text(encoding="utf-8")
        + "\n# different imported source\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(official_engine, "__file__", str(changed_source))
    assert source_identity()["source_sha256"] != before


@pytest.mark.parametrize("step", [1, 15, 60])
@pytest.mark.parametrize(
    "horizon,survives", [(9.119, True), (9.12, True), (9.120001, False)]
)
def test_official_exclusive_horizon_is_authoritative_without_ml(
    tmp_path: Path, step, horizon, survives
):
    request = AssessmentRequest(
        scenario=SimulationRequest(duration_hours=horizon, step_minutes=step)
    )
    result = assess(request, checkpoint_dir=tmp_path / "missing")
    assert result.physics.model_dump() == simulate(request.scenario).model_dump()
    assert result.physics.model_version == "lastlight-dispatch-1.0.0"
    assert result.physics.schema_version == "1.0.0"
    assert result.physics.summary.survived_full_window is survives
    assert result.neural.status == "unavailable"
    assert result.neural.estimate is None
    assert result.neural.model_version is None
    assert result.physics_authoritative is True
    assert result.engineering_clearance is False


def test_candidate_11_load_profiles_are_rejected_not_silently_projected():
    with pytest.raises(ValidationError):
        AssessmentRequest.model_validate(
            {"scenario": {"load": {"critical_profile_kw": [1.5] * 48}}}
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("physics_version", "lastlight-dispatch-1.1.0"),
        ("schema_version", "1.1.0"),
        ("feature_schema", "input-statistics-1"),
    ],
)
def test_callers_must_use_the_exact_official_and_feature_contract(field, value):
    with pytest.raises(ValidationError):
        AssessmentRequest.model_validate({"scenario": {}, field: value})
