"""Run the local API with an optional private shutdown signal for release checks."""

import argparse
import threading
import time
from pathlib import Path

import uvicorn


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--shutdown-file", type=Path)
    args = parser.parse_args()
    server = uvicorn.Server(
        uvicorn.Config(
            "services.simulation.api:app",
            host="127.0.0.1",
            port=args.port,
            log_level="info",
        )
    )

    if args.shutdown_file is not None:

        def watch() -> None:
            while not server.should_exit:
                if args.shutdown_file.exists():
                    server.should_exit = True
                    return
                time.sleep(0.1)

        threading.Thread(target=watch, daemon=True).start()

    server.run()
    return 0 if server.started else 1


if __name__ == "__main__":
    raise SystemExit(main())
