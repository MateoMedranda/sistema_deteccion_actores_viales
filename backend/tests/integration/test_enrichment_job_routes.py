from __future__ import annotations

import time


def test_image_source_can_create_private_enrichment_job(enrichment_client, auth_headers) -> None:
    client = enrichment_client
    uploaded = client.post("/api/v1/detections/images", headers=auth_headers, files={"image": ("road.jpg", __import__("tests.conftest", fromlist=["image_bytes"]).image_bytes(), "image/jpeg")})
    assert uploaded.status_code == 200
    source_id = uploaded.json()["request_id"]
    accepted = client.post("/api/v1/enrichment-jobs", headers=auth_headers, json={"source": {"kind": "image", "source_id": source_id}})
    assert accepted.status_code == 202, accepted.json()
    job_id = accepted.json()["enrichment_job_id"]
    for _ in range(30):
        state = client.get(f"/api/v1/enrichment-jobs/{job_id}", headers=auth_headers)
        if state.json()["status"] in {"completed", "failed", "cancelled"}: break
        time.sleep(.05)
    assert state.status_code == 200 and state.json()["status"] == "completed"
    result = client.get(f"/api/v1/enrichment-jobs/{job_id}/results", headers=auth_headers)
    assert result.status_code == 200
    item = result.json()["items"][0]
    assert item["plate_status"] == "read" and item["plate"]["text"] == "SYN123"
    assert item["track_id"] is None and item["detection_id"] == 1


def test_enrichment_source_is_owner_protected(client, auth_headers) -> None:
    uploaded = client.post("/api/v1/detections/images", headers=auth_headers, files={"image": ("road.jpg", __import__("tests.conftest", fromlist=["image_bytes"]).image_bytes(), "image/jpeg")})
    client.app.state.settings.api_keys = "other:other-secret"
    response = client.post("/api/v1/enrichment-jobs", headers={"X-API-Key": "other-secret"}, json={"source": {"kind": "image", "source_id": uploaded.json()["request_id"]}})
    assert response.status_code == 404
