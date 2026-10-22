import json
import os
import platform
import sys
from pathlib import Path
from statistics import quantiles
from time import perf_counter

import pytest

from tests.conftest import image_bytes


@pytest.mark.performance
def test_twenty_reference_requests_finish_under_five_seconds_with_fake_detector(
    client, auth_headers, record_property
):
    started = perf_counter()
    latencies_ms: list[float] = []
    samples: list[dict[str, int | str]] = []
    for _ in range(20):
        request_started = perf_counter()
        response = client.post(
            "/api/v1/detections/images",
            headers=auth_headers,
            files={"image": ("reference.jpg", image_bytes(), "image/jpeg")},
        )
        assert response.status_code == 200
        latencies_ms.append((perf_counter() - request_started) * 1000)
        state = client.app.state.service.request_state(response.json()["request_id"])
        assert state is not None
        samples.append(
            {
                "request_id": state.request_id,
                "validation_ms": state.validation_ms or 0,
                "inference_ms": state.inference_ms or 0,
                "annotation_ms": state.annotation_ms or 0,
                "total_ms": state.processing_time_ms or 0,
            }
        )

    p95_ms = quantiles(latencies_ms, n=20, method="inclusive")[18]
    report = {
        "hardware": platform.platform(),
        "python": sys.version,
        "model": client.app.state.service.detector.model_name,
        "device": client.app.state.settings.inference_device,
        "configuration": {
            "detector": "fake-yolov10s.pt",
            "media_type": "image/jpeg",
            "image_size": "40x40",
        },
        "p95_request_latency_ms": round(p95_ms, 2),
        "samples": samples,
    }
    report_path = Path(os.getenv("BENCHMARK_REPORT_PATH", ".runtime/benchmarks/reference-images.json"))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    record_property("hardware", platform.platform())
    record_property("model", client.app.state.service.detector.model_name)
    record_property("device", client.app.state.settings.inference_device)
    record_property("configuration", json.dumps(report["configuration"]))
    record_property("benchmark_report", str(report_path))
    record_property("validation_ms", str([sample["validation_ms"] for sample in samples]))
    record_property("inference_ms", str([sample["inference_ms"] for sample in samples]))
    record_property("annotation_ms", str([sample["annotation_ms"] for sample in samples]))
    record_property("total_p95_ms", f"{p95_ms:.2f}")
    assert perf_counter() - started <= 5
