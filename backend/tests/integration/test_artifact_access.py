from datetime import UTC, datetime, timedelta


def test_artifact_requires_auth_and_expiry(client, auth_headers):
    response = client.post(
        "/api/v1/detections/images",
        headers=auth_headers,
        files={"image": ("street.jpg", __import__("tests.conftest", fromlist=["image_bytes"]).image_bytes(), "image/jpeg")},
    )
    url = response.json()["annotated_image"]["url"]
    assert client.get(url).status_code == 401
    request_id = response.json()["request_id"]
    artifact = client.app.state.service.artifacts._artifacts[request_id]
    client.app.state.service.artifacts._artifacts[request_id] = artifact.__class__(
        request_id=artifact.request_id,
        path=artifact.path,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    assert client.get(url, headers=auth_headers).status_code == 410
