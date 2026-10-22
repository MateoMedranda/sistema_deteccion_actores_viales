def test_error_responses_follow_safe_shape(client, auth_headers):
    unauthorized = client.post("/api/v1/detections/images")
    invalid = client.post(
        "/api/v1/detections/images",
        headers=auth_headers,
        files={"image": ("bad.txt", b"x", "text/plain")},
    )
    for response in (unauthorized, invalid):
        assert response.status_code in {401, 415}
        body = response.json()
        assert set(body) == {"code", "message", "request_id"}
        assert "secret" not in str(body).lower()
