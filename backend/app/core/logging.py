import json
import logging
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        for key in (
            "request_id",
            "source_type",
            "status",
            "outcome",
            "elapsed_ms",
            "validation_ms",
            "inference_ms",
            "annotation_ms",
            "total_ms",
            "error_code",
            "job_id",
            "owner_key_id",
            "progress",
            "frame_ms",
            "memory_mb",
            "initial_memory_mb",
            "peak_memory_mb",
            "duration_ms",
            "model_version",
            "tracker",
            "ffmpeg_version",
            "upload_ms",
            "output_ms",
            "exception_type",
            "enrichment_job_id",
            "branch",
            "latency_ms",
            "eligible_vehicles",
            "expires_at",
            "retry_count",
            "candidate_count",
            "profile_id",
        ):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("road_actor_detection")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
