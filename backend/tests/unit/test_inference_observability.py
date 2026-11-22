import json
import logging
import time
import pytest
from app.core.logging import JsonFormatter
from app.services.inference_metrics import InferenceMetrics

@pytest.mark.parametrize("status", ["completed", "failed", "cancelled", "expired"])
def test_metrics_close_with_safe_correlated_measurements(caplog, status):
    logger = logging.getLogger("test.metrics")
    with caplog.at_level(logging.INFO, logger="test.metrics"):
        with InferenceMetrics(logger, "attributes", request_id="synthetic-source", job_id="job-1") as metric:
            metric.status = status
            if status == "failed":
                metric.error_code = "attribute_processing_failed"
    record = caplog.records[-1]
    payload = json.loads(JsonFormatter().format(record))
    assert payload["request_id"] == "synthetic-source"
    assert payload["job_id"] == "job-1" and payload["branch"] == "attributes"
    assert payload["duration_ms"] >= 0 and payload["memory_mb"] > 0
    assert payload["peak_memory_mb"] >= payload["memory_mb"]
    assert payload["status"] == status
    assert "frame_ms" not in payload and "exc_info" not in payload

def test_exception_message_and_paths_never_enter_metric_logs(caplog):
    logger = logging.getLogger("test.metrics")
    with caplog.at_level(logging.INFO, logger="test.metrics"):
        with pytest.raises(RuntimeError):
            with InferenceMetrics(logger, "detection", request_id="source"):
                raise RuntimeError("SECRET_PLATE_PRIVATE_PATH")
    assert caplog.records[-1].status == "failed"
    assert "SECRET_PLATE_PRIVATE_PATH" not in caplog.text


def test_enrichment_branches_emit_safe_source_and_job_context(caplog, monkeypatch):
    import numpy as np
    from app.services.enrichment_processing import EnrichmentProcessor
    from tests.enrichment_fixtures import FakeAttributes, FakeLocalizer, FakeReader
    logger = logging.getLogger("road_actor_detection")
    monkeypatch.setattr(logger, "propagate", True)
    with caplog.at_level(logging.INFO, logger="road_actor_detection"):
        EnrichmentProcessor(FakeAttributes(), FakeLocalizer(), FakeReader(), .7, .8).enrich(
            np.zeros((30, 40, 3), dtype=np.uint8), request_id="source", job_id="job")
    events = [r for r in caplog.records if r.message == "inference_measurement"]
    assert {r.branch for r in events} >= {"attributes", "plate_localization", "plate_ocr", "plate"}
    assert all(r.request_id == "source" and r.job_id == "job" for r in events)
    assert all(r.memory_mb > 0 and r.duration_ms >= 0 for r in events)
    assert "SYN123" not in caplog.text
