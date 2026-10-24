from fastapi.testclient import TestClient
from services.simulation.api import app


def test_openapi_exposes_strict_intelligence_contracts():
    with TestClient(app) as client:
        document = client.get("/openapi.json").json()
    assert "/api/v1/fragility/frontier" in document["paths"]
    assert "/api/v1/fragility/predict" in document["paths"]
    schema = document["components"]["schemas"]["SimulationRequest"]
    assert schema["additionalProperties"] is False
    assert "load" in schema["properties"]
