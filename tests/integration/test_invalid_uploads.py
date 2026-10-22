import logging

from tests.conftest import image_bytes


def test_invalid_uploads_are_safe(client, auth_headers):
    cases = [
        (("notes.txt", b"hello", "text/plain"), 415),
        (("corrupt.jpg", b"not-an-image", "image/jpeg"), 422),
    ]
    for file_value, status in cases:
        response = client.post("/api/v1/detections/images", headers=auth_headers, files={"image": file_value})
        assert response.status_code == status
        body = response.json()
        assert "request_id" in body
        assert "traceback" not in str(body).lower()


def test_large_dimensions_rejected(tmp_path, api_key):
    from fastapi.testclient import TestClient
    from app.core.config import Settings
    from app.main import create_app
    from tests.conftest import FakeDetector

    settings = Settings(api_key=api_key, max_image_pixels=100, temp_artifact_dir=tmp_path / "a")
    with TestClient(create_app(settings, FakeDetector())) as app_client:
        response = app_client.post(
            "/api/v1/detections/images",
            headers={"X-API-Key": api_key},
            files={"image": ("large.jpg", image_bytes(size=(20, 20)), "image/jpeg")},
        )
    assert response.status_code == 413


def test_rejected_upload_creates_a_safe_structured_log(client, auth_headers):
    records: list[logging.LogRecord] = []

    class CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logger = client.app.state.service.logger
    handler = CaptureHandler()
    logger.addHandler(handler)
    try:
        response = client.post(
            "/api/v1/detections/images",
            headers=auth_headers,
            files={"image": ("street.txt", image_bytes(), "image/jpeg")},
        )
    finally:
        logger.removeHandler(handler)

    assert response.status_code == 415
    rejected = next(record for record in records if record.getMessage() == "analysis_rejected")
    assert rejected.request_id == response.json()["request_id"]
    assert rejected.source_type == "image"
    assert rejected.status == "rejected"
    assert rejected.error_code == "unsupported_extension"
    assert isinstance(rejected.validation_ms, int)
