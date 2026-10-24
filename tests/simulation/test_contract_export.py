from fastapi.testclient import TestClient
from services.simulation.api import app
from services.simulation.fixtures import semantic_json


def test_openapi_exposes_strict_intelligence_contracts():
    with TestClient(app) as client:
        document = client.get("/openapi.json").json()
    assert "/api/v1/fragility/frontier" in document["paths"]
    assert "/api/v1/fragility/predict" in document["paths"]
    schema = document["components"]["schemas"]["SimulationRequest"]
    assert schema["additionalProperties"] is False
    assert "load" in schema["properties"]


def test_schema_union_order_is_semantic_but_trace_order_is_preserved():
    first = {"anyOf": [{"type": "string"}, {"type": "null"}]}
    second = {"anyOf": [{"type": "null"}, {"type": "string"}]}
    assert semantic_json(first) == semantic_json(second)
    assert semantic_json({"trace": [1, 2]}) != semantic_json({"trace": [2, 1]})
