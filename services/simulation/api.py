"""Local FastAPI boundary; independent of web rendering and ML."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from . import MODEL_VERSION
from .design_search import DesignSearchRequest, DesignSearchResult, search_designs
from .engine import EnergyBalanceError, compare, simulate
from .frontier import FrontierRequest, physics_frontier
from .schemas import (
    ComparisonRequest,
    ComparisonResult,
    ErrorBody,
    ErrorDetail,
    ErrorResponse,
    Health,
    SimulationRequest,
    SimulationResult,
)

app = FastAPI(
    title="LASTLIGHT Physics API",
    version=MODEL_VERSION,
    description="Deterministic single-bus energy dispatch. kW power; DC kWh storage; UTC time.",
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def error_response(
    code: str, message: str, status: int, details: list[ErrorDetail] | None = None
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorBody(code=code, message=message, details=details or [])
    )
    return JSONResponse(status_code=status, content=body.model_dump(mode="json"))


@app.exception_handler(RequestValidationError)
async def validation_error(
    _request: Request, exception: RequestValidationError
) -> JSONResponse:
    # Never echo raw request values: NaN and exception objects are not JSON-safe.
    details = [
        ErrorDetail(location=list(e["loc"]), message=e["msg"], type=e["type"])
        for e in exception.errors()
    ]
    return error_response("validation_error", "Request validation failed", 422, details)


@app.exception_handler(HTTPException)
async def http_error(_request: Request, exception: HTTPException) -> JSONResponse:
    response = error_response(
        "http_error", str(exception.detail), exception.status_code
    )
    response.headers.update(exception.headers or {})
    return response


@app.exception_handler(EnergyBalanceError)
async def balance_error(
    _request: Request, _exception: EnergyBalanceError
) -> JSONResponse:
    return error_response(
        "energy_balance_error", "Simulation failed an internal physical invariant", 500
    )


@app.exception_handler(Exception)
async def unexpected_error(_request: Request, exception: Exception) -> JSONResponse:
    logging.getLogger(__name__).error("Unhandled simulation error", exc_info=exception)
    return error_response(
        "internal_error", "Simulation service encountered an internal error", 500
    )


@app.get("/health", response_model=Health)
def health() -> Health:
    return Health()


@app.post("/api/v1/simulations", response_model=SimulationResult)
def run_simulation(request: SimulationRequest) -> SimulationResult:
    return simulate(request)


@app.post("/api/v1/comparisons", response_model=ComparisonResult)
def run_comparison(request: ComparisonRequest) -> ComparisonResult:
    return compare(request)


@app.post("/api/v1/frontiers")
def run_frontier(request: FrontierRequest) -> dict:
    """Return only official-physics cells; incompatible ML proposals stay absent."""
    return physics_frontier(request)


@app.post("/api/v1/design-search", response_model=DesignSearchResult)
def run_design_search(request: DesignSearchRequest) -> DesignSearchResult:
    """Test every supplied capacity; select the smallest critical-load survivor."""
    return search_designs(request)
