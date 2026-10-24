"""Additive intelligence on the official app; no scientific imports at startup."""

from copy import copy
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

from .adapter import DEFAULT_CHECKPOINT
from .api import create_router


def intelligence_openapi(app: FastAPI) -> dict:
    routes = []
    for route in app.routes:
        if (
            isinstance(route, APIRoute)
            and route.path != "/api/v1/intelligence/openapi.json"
        ):
            public = copy(route)
            public.include_in_schema = True
            routes.append(public)
    return get_openapi(
        title="LASTLIGHT unified physics and intelligence",
        version="lastlight-intelligence-1",
        description="Official v1 physics is authoritative. ML estimates and historical forecasts have separate identities and provenance.",
        routes=routes,
    )


def install_intelligence(app: FastAPI) -> None:
    app.state.fragility_checkpoint_dir = Path(
        os.environ.get("LASTLIGHT_FRAGILITY_CHECKPOINT", str(DEFAULT_CHECKPOINT))
    )
    # Standalone physics installs copy only services/simulation. Keep their exact
    # frozen /openapi.json, while publishing the complete additive contract below.
    app.include_router(create_router(), include_in_schema=False)

    @app.get("/api/v1/intelligence/openapi.json", include_in_schema=False)
    def complete_contract() -> dict:
        return intelligence_openapi(app)
