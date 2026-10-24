"""Identify the actual official source, without changing its version strings."""

import hashlib
import json
from pathlib import Path

from services.simulation import MODEL_VERSION, SCHEMA_VERSION
from services import simulation as official_package
from services.simulation import engine as official_engine, schemas as official_schemas
from services.simulation.schemas import SimulationRequest

OFFICIAL_PHYSICS = "lastlight-dispatch-1.0.0"
OFFICIAL_SCHEMA = "1.0.0"


def source_identity() -> dict[str, str]:
    if MODEL_VERSION != OFFICIAL_PHYSICS or SCHEMA_VERSION != OFFICIAL_SCHEMA:
        raise ValueError(
            "Bridge requires the official v1 runtime, not a relabelled candidate engine"
        )
    files = {
        "__init__.py": official_package,
        "schemas.py": official_schemas,
        "engine.py": official_engine,
    }
    sources = {
        name: hashlib.sha256(
            Path(module.__file__).read_text(encoding="utf-8").encode()
        ).hexdigest()
        for name, module in files.items()
    }
    digest = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
    schema = json.dumps(
        SimulationRequest.model_json_schema(), sort_keys=True, separators=(",", ":")
    )
    return {
        "physics_version": MODEL_VERSION,
        "schema_version": SCHEMA_VERSION,
        "source_sha256": digest,
        "request_schema_sha256": hashlib.sha256(schema.encode()).hexdigest(),
    }
