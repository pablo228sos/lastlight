"""Proposed optional router. No mutation of the official Physics API application."""

from pathlib import Path

from fastapi import APIRouter, FastAPI

from .adapter import DEFAULT_CHECKPOINT, assess
from .candidates import suggest
from .contracts import Assessment, AssessmentRequest, CandidateRequest, CandidateResult


def create_router(checkpoint_dir: Path | None = None) -> APIRouter:
    directory = (
        Path(checkpoint_dir) if checkpoint_dir is not None else DEFAULT_CHECKPOINT
    )
    router = APIRouter(
        prefix="/api/v1/ml/fragility", tags=["Optional official-v1 ML bridge"]
    )

    @router.post("/assess", response_model=Assessment)
    def assessment(request: AssessmentRequest) -> Assessment:
        return assess(request, directory)

    @router.post("/candidates", response_model=CandidateResult)
    def candidates(request: CandidateRequest) -> CandidateResult:
        return suggest(request, directory)

    return router


# Isolated local research service. Production owner can optionally mount create_router().
app = FastAPI(title="LASTLIGHT optional official-v1 ML bridge", version="1")
app.include_router(create_router())
