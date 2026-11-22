from tests.conftest import isolated_settings
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_health_and_authentication(client):
    assert client.get("/health/live").json() == {"status": "alive"}
    assert client.get("/health/ready").json() == {"status": "ready"}
    response = client.post("/api/v1/detections/images")
    assert response.status_code == 401


def test_video_readiness_reports_tool_state(client):
    response = client.get("/health/video-ready")
    assert response.status_code in {200, 503}


def test_video_upload_is_rejected_before_multipart_parsing(client):
    response = client.post("/api/v1/video-jobs", content=b"not-a-video")
    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_service_without_model_is_not_ready(tmp_path):
    settings = isolated_settings(
        tmp_path, api_key="test",
        model_weights_path=tmp_path / "missing-model.pt",
        temp_artifact_dir=tmp_path / "artifacts",
    )
    with TestClient(create_app(settings=settings)) as client:
        assert client.get("/health/ready").status_code == 503
