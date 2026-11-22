from __future__ import annotations

from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import Settings
from app.domain.models import Detection
from app.main import create_app


def isolated_settings(root, **overrides):
    """Keep test lifespans away from the running service's durable files."""
    values = {
        "_env_file": None,
        "temp_artifact_dir": root / "artifacts",
        "video_job_db_path": root / "video-jobs.sqlite3",
        "video_temp_dir": root / "video-jobs",
        "count_job_db_path": root / "count-jobs.sqlite3",
        "count_temp_dir": root / "count-jobs",
        "enrichment_job_db_path": root / "enrichment-jobs.sqlite3",
        "enrichment_temp_dir": root / "enrichment",
    }
    values.update(overrides)
    return Settings(**values)


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
        _env_file=None,
        api_key=api_key,
        temp_artifact_dir=tmp_path / "artifacts",
        video_job_db_path=tmp_path / "video-jobs.sqlite3",
        video_temp_dir=tmp_path / "video-jobs",
        count_job_db_path=tmp_path / "count-jobs.sqlite3",
        count_temp_dir=tmp_path / "count-jobs",
        enrichment_job_db_path=tmp_path / "enrichment-jobs.sqlite3",
        enrichment_temp_dir=tmp_path / "enrichment",
    )
    with TestClient(create_app(settings=settings, detector=FakeDetector())) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(api_key):
    return {"X-API-Key": api_key}


@pytest.fixture
def enrichment_client(tmp_path, api_key, monkeypatch):
    from tests.enrichment_fixtures import FakeAttributes, FakeLocalizer, FakeReader
    monkeypatch.setattr("app.core.lifespan.EfficientNetAttributeExtractor", lambda *a: FakeAttributes())
    monkeypatch.setattr("app.core.lifespan.YOLOv8PlateLocalizer", lambda *a: FakeLocalizer())
    monkeypatch.setattr("app.core.lifespan.PaddlePlateReader", lambda *a: FakeReader())
    settings = Settings(_env_file=None, api_key=api_key,
        temp_artifact_dir=tmp_path/"artifacts", video_job_db_path=tmp_path/"video.sqlite3", video_temp_dir=tmp_path/"video",
        count_job_db_path=tmp_path/"count.sqlite3", count_temp_dir=tmp_path/"count",
        enrichment_job_db_path=tmp_path/"enrichment.sqlite3", enrichment_temp_dir=tmp_path/"sources",
        attribute_model_weights_path=tmp_path/"fake.pt", attribute_model_manifest_path=tmp_path/"fake.json",
        plate_model_weights_path=tmp_path/"plate.pt")
    with TestClient(create_app(settings=settings, detector=FakeDetector())) as test_client:
        yield test_client

@pytest.fixture
def annotation_controls():
    from tests.annotation_fixtures import Clock,Barrier,CountedReader
    return {"clock":Clock(),"barrier":Barrier(),"reader":CountedReader(),"owners":("owner-alpha","owner-beta")}


@pytest.fixture
def exploration_controls():
    from tests.fixtures_008 import Clock, Barrier, OWNERS
    return {"clock":Clock(),"barrier":Barrier(),"owners":OWNERS}
