from tests.conftest import FakeDetector, image_bytes


def test_analyze_valid_image_and_retrieve_annotation(client, auth_headers):
    response = client.post(
        "/api/v1/detections/images",
        headers=auth_headers,
        files={"image": ("street.jpg", image_bytes(), "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["detections"][0]["class_name"] == "Car"
    assert body["detections"][0]["confidence"] == 0.91
    annotation = client.get(body["annotated_image"]["url"], headers=auth_headers)
    assert annotation.status_code == 200
    assert annotation.headers["content-type"].startswith("image/jpeg")


def test_valid_image_can_return_no_detections(tmp_path, api_key):
    from fastapi.testclient import TestClient
    from app.core.config import Settings
    from app.main import create_app

    with TestClient(create_app(Settings(api_key=api_key, temp_artifact_dir=tmp_path / "a"), FakeDetector([]))) as app_client:
        response = app_client.post(
            "/api/v1/detections/images",
            headers={"X-API-Key": api_key},
            files={"image": ("empty.jpg", image_bytes(), "image/jpeg")},
        )
    assert response.status_code == 200
    assert response.json()["detections"] == []


def test_each_analysis_has_a_unique_request_id(client, auth_headers):
    first = client.post(
        "/api/v1/detections/images",
        headers=auth_headers,
        files={"image": ("first.jpg", image_bytes(), "image/jpeg")},
    )
    second = client.post(
        "/api/v1/detections/images",
        headers=auth_headers,
        files={"image": ("second.jpg", image_bytes(), "image/jpeg")},
    )
    assert first.json()["request_id"] != second.json()["request_id"]
