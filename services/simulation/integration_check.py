"""Real launcher/HTTP release check, using only the Python standard library.

Run from the repository root: python -m services.simulation.integration_check.
A temporary source copy guarantees fresh setup without altering your environment.
On Windows this executes start.cmd, not a Linux substitute for that launcher.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "docs" / "physics" / "fixtures"
OPENER = build_opener(ProxyHandler({}))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def http(base: str, path: str, body=None, *, method=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    request = Request(
        base + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        response = OPENER.open(request, timeout=5)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read().decode("utf-8")
        content = (
            json.loads(raw)
            if "application/json" in response.headers.get("Content-Type", "")
            else raw
        )
        return response.code, response.headers, content


def fresh_source(destination: Path) -> Path:
    service = destination / "services" / "simulation"
    service.mkdir(parents=True)
    for source in (ROOT / "services" / "simulation").iterdir():
        if source.is_file() and (
            source.suffix in {".py", ".lock", ".txt"} or source.name == "start.cmd"
        ):
            shutil.copy2(source, service / source.name)
    return destination


def launcher(root: Path, *arguments: str) -> list[str]:
    if os.name == "nt":
        # Relative path contains no spaces; cwd may contain spaces. No shell=True.
        return [
            os.environ.get("COMSPEC", "cmd.exe"),
            "/d",
            "/c",
            r"services\simulation\start.cmd",
            *arguments,
        ]
    return [
        sys.executable,
        str(root / "services" / "simulation" / "run.py"),
        *arguments,
    ]


def setup(root: Path, log: Path, *arguments: str) -> None:
    with log.open("w", encoding="utf-8") as output:
        result = subprocess.run(
            launcher(root, *arguments, "--setup-only"),
            cwd=root,
            stdout=output,
            stderr=subprocess.STDOUT,
            timeout=240,
        )
    require(result.returncode == 0, f"Fresh setup failed; see {log}")


def closed(port: int) -> bool:
    with socket.socket() as connection:
        connection.settimeout(0.2)
        return connection.connect_ex(("127.0.0.1", port)) != 0


def start(root: Path, port: int, log: Path):
    require(closed(port), f"Port {port} is in use; choose --port")
    shutdown_file = log.with_suffix(".shutdown")
    shutdown_file.unlink(missing_ok=True)
    environment = {**os.environ, "PIP_NO_INDEX": "1", "PYTHONUNBUFFERED": "1"}
    options = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    with log.open("w", encoding="utf-8") as output:
        process = subprocess.Popen(
            launcher(
                root,
                "--offline",
                "--port",
                str(port),
                "--shutdown-file",
                str(shutdown_file),
            ),
            cwd=root,
            stdout=output,
            stderr=subprocess.STDOUT,
            env=environment,
            **options,
        )
    return process


def ready(process, base: str, log: Path) -> None:
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        require(process.poll() is None, f"Launcher exited before readiness; see {log}")
        try:
            status, _, body = http(base, "/health")
            if status == 200 and body.get("status") == "ok":
                return
        except (OSError, URLError):
            pass
        time.sleep(0.1)
    raise RuntimeError(f"API readiness timeout; see {log}")


def stop(process, port: int, log: Path) -> int:
    if process.poll() is None:
        log.with_suffix(".shutdown").write_text("stop\n", encoding="utf-8")
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None and closed(port):
            break
        time.sleep(0.1)
    else:
        # Cleanup is a failed check, never evidence of a graceful shutdown.
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True
            )
        else:
            process.kill()
        raise RuntimeError(f"Launcher/server did not stop cleanly; see {log}")
    require(
        "Application shutdown complete." in log.read_text(encoding="utf-8"),
        f"Missing graceful shutdown; see {log}",
    )
    return process.returncode


def verify_http(base: str, checks: list[str]) -> dict:
    expected = read_json(FIXTURES / "baseline.result.json")

    def post(path, body, result):
        status, _, actual = http(base, path, body)
        require(status == 200 and actual == result, f"Live fixture mismatch: {path}")
        return actual

    status, _, health = http(base, "/health")
    require(
        status == 200
        and health
        == {
            "status": "ok",
            "model_version": expected["model_version"],
            "schema_version": expected["schema_version"],
        },
        "Health/version mismatch",
    )
    checks.append("health and frozen versions")
    status, _, spec = http(base, "/openapi.json")
    require(
        status == 200 and spec == read_json(FIXTURES.parent / "openapi.json"),
        "OpenAPI drift",
    )
    checks.append("live OpenAPI equals frozen contract")
    baseline = post("/api/v1/simulations", {}, expected)
    post("/api/v1/simulations", read_json(FIXTURES / "baseline.request.json"), expected)
    checks.append("minimal/full baseline requests reproduce every fixture interval")
    require(baseline["summary"]["critical_survival_hours"] == 9.12, "Baseline autonomy")
    comparison = post(
        "/api/v1/comparisons",
        read_json(FIXTURES / "comparison.request.json"),
        read_json(FIXTURES / "comparison.result.json"),
    )
    require(
        comparison["upgraded"]["summary"]["first_failure_utc"] is None,
        "12h upgrade must be censored",
    )
    require(
        comparison["upgraded"]["summary"]["critical_survival_hours"] is None,
        "Analytic autonomy is not observed failure",
    )
    checks.append("12h comparison fixture, including null observed upgrade failure")
    regressions = read_json(FIXTURES / "regression-16h.json")
    for upgrade, survival in [("battery_36_kwh", 13.68), ("full_precharge", 12.16)]:
        status, _, actual = http(
            base,
            "/api/v1/comparisons",
            {"baseline": {"duration_hours": 16}, "upgrade": upgrade},
        )
        require(
            status == 200
            and actual["baseline"] == regressions["baseline"]
            and actual["upgraded"] == regressions[upgrade],
            f"16h {upgrade} fixture mismatch",
        )
        require(
            actual["upgraded"]["summary"]["critical_survival_hours"] == survival,
            f"16h {upgrade} autonomy",
        )
    checks.append("both 16h upgrades reproduce full frozen traces")
    design = post(
        "/api/v1/design-search",
        read_json(FIXTURES / "design-search.request.json"),
        read_json(FIXTURES / "design-search.result.json"),
    )
    require(design["selected_capacity_kwh"] == 32, "Design search capacity ranking")
    for candidate in design["candidates"]:
        status, _, replay = http(base, "/api/v1/simulations", candidate["input"])
        digest = hashlib.sha256(
            json.dumps(
                replay, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode("utf-8")
        ).hexdigest()
        require(
            status == 200
            and replay["summary"] == candidate["summary"]
            and replay["run_id"] == candidate["simulation_run_id"]
            and replay["input_hash"] == candidate["simulation_input_hash"]
            and digest == candidate["simulation_result_hash"],
            "Design candidate does not reproduce the full official trace",
        )
    checks.append(
        "design search selects 32 kWh; every candidate replays full official result"
    )
    precharge = post(
        "/api/v1/design-search",
        read_json(FIXTURES / "design-search-precharge.request.json"),
        read_json(FIXTURES / "design-search-precharge.result.json"),
    )
    require(precharge["selected_capacity_kwh"] == 24, "Precharged design survival")
    checks.append("24 kWh at full precharge survives the 12h design target")
    post(
        "/api/v1/frontiers",
        {},
        read_json(ROOT / "apps/web/src/data/frontier.result.json"),
    )
    checks.append("existing live frontier equals the approved offline map")
    for origin in [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]:
        status, headers, _ = http(
            base,
            "/api/v1/simulations",
            method="OPTIONS",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        require(
            status == 200 and headers.get("Access-Control-Allow-Origin") == origin,
            f"CORS {origin}",
        )
    status, headers, _ = http(
        base,
        "/api/v1/simulations",
        method="OPTIONS",
        headers={
            "Origin": "https://example.invalid",
            "Access-Control-Request-Method": "POST",
        },
    )
    require(
        status == 400 and headers.get("Access-Control-Allow-Origin") is None,
        "External CORS origin allowed",
    )
    checks.append("all four Vite origins allowed; external preflight rejected")
    for path, body in [
        ("/api/v1/simulations", {"battery": {"initial_soc": 1.1}}),
        ("/api/v1/comparisons", {"upgrade": "unknown"}),
        (
            "/api/v1/design-search",
            {"scenario": {}, "outage_hours": 12, "candidate_capacities_kwh": [0]},
        ),
    ]:
        status, headers, actual = http(
            base, path, body, headers={"Origin": "http://localhost:5173"}
        )
        require(
            status == 422
            and actual["error"]["code"] == "validation_error"
            and headers.get("Access-Control-Allow-Origin") == "http://localhost:5173",
            "Invalid input/error CORS mismatch",
        )
        if path.endswith("simulations"):
            require(
                actual == read_json(FIXTURES / "validation-error.json"),
                "Frozen validation error drift",
            )
    for path, code in [("/missing", 404), ("/api/v1/simulations", 405)]:
        status, _, body = http(base, path)
        require(
            status == code and body["error"]["code"] == "http_error",
            f"HTTP {code} contract",
        )
    checks.append("simulation/comparison/design validation errors and HTTP 404/405")
    post("/api/v1/simulations", {}, expected)
    checks.append("repeated request is exactly reproducible")
    return {
        "baseline": baseline["summary"],
        "run_id": baseline["run_id"],
        "schema_version": baseline["schema_version"],
        "model_version": baseline["model_version"],
        "design_search_id": design["search_id"],
        "design_result_hash": design["result_hash"],
        "selected_capacity_kwh": design["selected_capacity_kwh"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "services/simulation/.integration-evidence",
    )
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--wheelhouse",
        type=Path,
        help="Also prove first-time offline installation from hashed wheels",
    )
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be in 1..65535")
    evidence = args.output_dir.resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    report = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python": sys.version,
        "windows_launcher_executed": os.name == "nt",
        "checks": [],
        "success": False,
        "source_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / "services/simulation").iterdir())
            if p.is_file() and (p.suffix in {".py", ".lock"} or p.name == "start.cmd")
        },
    }
    checks = report["checks"]
    try:
        with tempfile.TemporaryDirectory(prefix="lastlight release ") as temporary:
            checkout = fresh_source(Path(temporary) / "fresh setup")
            install_args = (
                ("--offline", "--wheelhouse", str(args.wheelhouse.resolve()))
                if args.wheelhouse
                else ()
            )
            setup(checkout, evidence / "fresh-install.log", *install_args)
            checks.append(
                "fresh hash-locked launcher installation in path containing spaces"
            )
            base = f"http://127.0.0.1:{args.port}"
            for phase in ["offline-start", "offline-restart"]:
                log = evidence / f"{phase}.log"
                process = start(checkout, args.port, log)
                try:
                    ready(process, base, log)
                    report[phase] = verify_http(base, checks)
                finally:
                    report[f"{phase}_exit_code"] = stop(process, args.port, log)
                checks.append(f"{phase}: graceful shutdown and released port")
            if args.wheelhouse:
                offline = fresh_source(Path(temporary) / "first offline setup")
                setup(
                    offline,
                    evidence / "offline-install.log",
                    "--offline",
                    "--wheelhouse",
                    str(args.wheelhouse.resolve()),
                )
                checks.append(
                    "first-time offline install from local hash-verified wheels"
                )
        report["success"] = True
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
        print(f"Integration check FAILED: {error}", file=sys.stderr)
    finally:
        (evidence / "report.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    print(f"{len(checks)} checks recorded; evidence: {evidence}")
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
