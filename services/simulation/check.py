"""Shared local/CI verification: python -m services.simulation.check."""

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["COVERAGE_FILE"] = str(Path(__file__).resolve().parent / ".coverage")
    env["HYPOTHESIS_STORAGE_DIRECTORY"] = str(
        Path(__file__).resolve().parent / ".hypothesis"
    )
    commands = [
        ["ruff", "check", "services/simulation", "tests/simulation"],
        ["ruff", "format", "--check", "services/simulation", "tests/simulation"],
        ["services.simulation.fixtures", "--check"],
        [
            "pytest",
            "tests/simulation",
            "-q",
            "--cov=services.simulation.engine",
            "--cov=services.simulation.schemas",
            "--cov=services.simulation.api",
            "--cov-report=term-missing",
            "--cov-fail-under=95",
        ],
    ]
    for command in commands:
        result = subprocess.run([sys.executable, "-m", *command], cwd=root, env=env)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
