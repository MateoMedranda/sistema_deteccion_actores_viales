def test_image_policy_reports_only_existing_configured_limits(client):
    settings=client.app.state.settings
    settings.max_upload_bytes=2*1024*1024;settings.max_image_pixels=3_000_000
    response=client.get("/health/image-policy")
    assert response.status_code==200
    assert response.json()=={"media_types":["image/jpeg","image/png"],"max_upload_bytes":2*1024*1024,"max_image_pixels":3_000_000}
    settings.max_upload_bytes=5*1024*1024
    assert client.get("/health/image-policy").json()["max_upload_bytes"]==5*1024*1024
