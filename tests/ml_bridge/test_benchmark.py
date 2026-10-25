from types import SimpleNamespace

import pytest

from ml_bridge.benchmark import require_real_model


@pytest.mark.parametrize(
    "case,result",
    [
        ("neural", SimpleNamespace(status="unavailable")),
        ("forecast", SimpleNamespace(neural_status="incompatible_checkpoint")),
    ],
)
def test_benchmark_refuses_to_report_fallback_as_neural_inference(case, result):
    with pytest.raises(RuntimeError, match="not an inference measurement"):
        require_real_model(case, result)
