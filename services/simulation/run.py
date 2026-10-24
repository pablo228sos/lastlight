"""One-command local server bootstrap; standard library only, Python 3.12+.

Use start.cmd on Windows, or `python services/simulation/run.py` elsewhere.
After initial installation the cached environment needs no network. To install
from pre-downloaded wheels, use --offline --wheelhouse <directory>.
"""

import argparse
import hashlib
import os
import subprocess
import sys
import venv
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline", action="store_true", help="Disable package-index access"
    )
    parser.add_argument(
        "--wheelhouse", type=Path, help="Local wheels for offline setup"
    )
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Install/verify the environment, then exit",
    )
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        parser.error(
            "Python 3.12 or newer is required; Python 3.12 is the verified runtime"
        )
    if not 1 <= args.port <= 65535:
        parser.error("--port must be in 1..65535")
    root = Path(__file__).resolve().parent
    environment = root / ".venv"
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    requirements = root / "requirements.lock"
    marker = environment / "lastlight-requirements.sha256"
    digest = hashlib.sha256(requirements.read_bytes()).hexdigest()
    try:
        if not python.exists():
            print("Creating isolated LASTLIGHT Python environment", flush=True)
            venv.EnvBuilder(with_pip=True).create(environment)
        if not marker.exists() or marker.read_text(encoding="utf-8") != digest:
            command = [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--require-hashes",
                "-r",
                str(requirements),
            ]
            if args.offline:
                command.append("--no-index")
            if args.wheelhouse:
                command.extend(["--find-links", str(args.wheelhouse.resolve())])
            subprocess.run(command, check=True)
            marker.write_text(digest, encoding="utf-8")
        subprocess.run([str(python), "-m", "pip", "check"], check=True)
        if args.setup_only:
            return 0
        print(
            f"LASTLIGHT API: http://127.0.0.1:{args.port} | docs: /docs | offline schema: /openapi.json",
            flush=True,
        )
        return subprocess.call(
            [
                str(python),
                "-m",
                "uvicorn",
                "services.simulation.api:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(args.port),
            ],
            cwd=root.parents[1],
        )
    except (OSError, subprocess.CalledProcessError) as error:
        print(
            f"Setup failed: {error}. For offline setup, prepare local wheels first; see docs/physics/README.md.",
            file=sys.stderr,
        )
        return 1
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
