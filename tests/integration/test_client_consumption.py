from tests.conftest import image_bytes


def test_client_can_consume_only_public_response_fields(client, auth_headers):
    for _ in range(20):
        response = client.post(
            "/api/v1/detections/images",
            headers=auth_headers,
            files={"image": ("street.jpg", image_bytes(), "image/jpeg")},
        )
        body = response.json()
        detection = body["detections"][0]
        assert set(detection) == {"detection_id", "class_id", "class_name", "confidence", "bbox"}
        assert body["annotated_image"]["url"].startswith("/api/")
