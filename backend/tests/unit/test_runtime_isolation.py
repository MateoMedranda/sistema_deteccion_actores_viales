from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import FakeDetector, isolated_settings


def test_test_lifespan_does_not_remove_running_service_files(tmp_path, monkeypatch):
    service_output = tmp_path / "service" / "output"
    service_output.mkdir(parents=True)
    existing_video = service_output / "existing.mp4"
    existing_video.write_bytes(b"existing-private-result")
    monkeypatch.setenv("VIDEO_TEMP_DIR", str(service_output.parent))
    settings = isolated_settings(tmp_path / "test", api_key="test")
    with TestClient(create_app(settings, FakeDetector())) as client:
        assert client.get("/health/live").status_code == 200
    assert existing_video.read_bytes() == b"existing-private-result"
