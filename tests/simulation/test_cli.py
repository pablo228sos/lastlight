import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def call(*arguments):
    return subprocess.run(
        [sys.executable, "-m", "services.simulation", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )


@pytest.mark.parametrize(
    "operation,path",
    [
        ("simulate", "baseline"),
        ("compare", "comparison"),
    ],
)
def test_offline_cli_emits_the_frozen_full_trace(operation, path):
    actual = call(operation, f"docs/physics/fixtures/{path}.request.json")
    assert actual.returncode == 0, actual.stderr
    expected = json.loads(
        (ROOT / f"docs/physics/fixtures/{path}.result.json").read_text(encoding="utf-8")
    )
    assert json.loads(actual.stdout) == expected


def test_cli_supports_utf8_bom_and_offset_timestamps(tmp_path):
    request = tmp_path / "windows-request.json"
    request.write_text(
        '{"start_utc":"2026-01-01T06:00:00+06:00"}', encoding="utf-8-sig"
    )
    response = call("simulate", str(request))
    assert response.returncode == 0, response.stderr
    assert json.loads(response.stdout)["input"]["start_utc"] == "2026-01-01T00:00:00Z"


def test_cli_validation_and_missing_file_exit_nonzero(tmp_path):
    missing = call("simulate", str(tmp_path / "missing.json"))
    assert missing.returncode == 2 and missing.stderr and not missing.stdout
    bad = tmp_path / "bad.json"
    bad.write_text('{"battery":{"capacity_kwh":0}}', encoding="utf-8")
    invalid = call("simulate", str(bad))
    assert invalid.returncode == 2 and invalid.stderr and not invalid.stdout
