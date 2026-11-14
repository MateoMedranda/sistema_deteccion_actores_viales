import logging

from app.core.logging import JsonFormatter


def test_video_metric_fields_are_serialized() -> None:
    record = logging.LogRecord("test", logging.INFO, "", 0, "video_frame_processed", (), None)
    record.job_id = "job"
    record.frame_ms = 12
    record.memory_mb = 100.5
    rendered = JsonFormatter().format(record)
    assert '"job_id": "job"' in rendered
    assert '"memory_mb": 100.5' in rendered
