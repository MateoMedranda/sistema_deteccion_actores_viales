def test_image_health_regression(client) -> None:
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 200
