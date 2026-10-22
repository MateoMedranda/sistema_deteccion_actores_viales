from tests.conftest import image_bytes


def test_success_response_has_required_detection_contract(client, auth_headers):
    response = client.post(
        "/api/v1/detections/images",
        headers=auth_headers,
        files={"image": ("street.jpg", image_bytes(), "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert {"request_id", "status", "processing_time_ms", "image", "detections", "annotated_image"} <= body.keys()
    assert {"x_min", "y_min", "x_max", "y_max"} <= body["detections"][0]["bbox"].keys()


def test_empty_detection_response_is_successful(tmp_path, api_key):
    from fastapi.testclient import TestClient
    from app.core.config import Settings
    from app.main import create_app
    from tests.conftest import FakeDetector

    with TestClient(create_app(Settings(api_key=api_key, temp_artifact_dir=tmp_path / "a"), FakeDetector([]))) as app_client:
        response = app_client.post(
            "/api/v1/detections/images",
            headers={"X-API-Key": api_key},
            files={"image": ("street.jpg", image_bytes(), "image/jpeg")},
        )
    assert response.status_code == 200
    assert response.json()["detections"] == []
