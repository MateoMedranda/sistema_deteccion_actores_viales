from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_health_and_authentication(client):
    assert client.get("/health/live").json() == {"status": "alive"}
    assert client.get("/health/ready").json() == {"status": "ready"}
    response = client.post("/api/v1/detections/images")
    assert response.status_code == 401


def test_service_without_model_is_not_ready(tmp_path):
    settings = Settings(api_key="test", temp_artifact_dir=tmp_path / "artifacts")
    with TestClient(create_app(settings=settings)) as client:
        assert client.get("/health/ready").status_code == 503
