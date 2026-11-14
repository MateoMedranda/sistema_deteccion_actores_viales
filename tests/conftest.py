from __future__ import annotations

from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import Settings
from app.domain.models import Detection
from app.main import create_app


class FakeDetector:
    model_name = "fake-yolov10s.pt"

    def __init__(self, detections: list[Detection] | None = None) -> None:
        self.detections = detections if detections is not None else [
            Detection(class_id=0, class_name="Car", confidence=0.91, x_min=5, y_min=5, x_max=30, y_max=30)
        ]

    def detect(self, image):
        return self.detections


def image_bytes(format_name: str = "JPEG", size: tuple[int, int] = (40, 40)) -> bytes:
    image = Image.new("RGB", size, color=(100, 100, 100))
    output = BytesIO()
    image.save(output, format=format_name)
    return output.getvalue()


@pytest.fixture
def api_key() -> str:
    return "test-api-key"


@pytest.fixture
def client(tmp_path, api_key):
    settings = Settings(
        api_key=api_key,
        temp_artifact_dir=tmp_path / "artifacts",
        video_job_db_path=tmp_path / "video-jobs.sqlite3",
        video_temp_dir=tmp_path / "video-jobs",
        count_job_db_path=tmp_path / "count-jobs.sqlite3",
        count_temp_dir=tmp_path / "count-jobs",
    )
    with TestClient(create_app(settings=settings, detector=FakeDetector())) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(api_key):
    return {"X-API-Key": api_key}
