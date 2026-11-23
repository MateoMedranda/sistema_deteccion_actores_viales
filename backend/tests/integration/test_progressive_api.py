import time
from tests.fixtures_progressive import video


def test_progressive_pipeline_range_withdraw(enrichment_client, tmp_path, auth_headers):
    path = video(tmp_path / "sample.mp4")
    response = enrichment_client.post(
        "/api/v1/video-jobs?presentation=progressive",
        headers=auth_headers,
        files={"video": ("sample.mp4", path.read_bytes(), "video/mp4")},
    )
    assert response.status_code == 202, response.text
    job = response.json()["job_id"]
    base = f"/api/v1/video-jobs/{job}/playback"
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        result = enrichment_client.get(base, headers=auth_headers)
        assert result.status_code == 200, result.text
        state = result.json()
        if state["analysis_state"] in ("complete", "partial_failed"):
            break
        time.sleep(0.05)
    assert state["analysis_state"] == "complete", state
    assert state["frames_published"] == 12
    end = state["available_until_us"]
    page = enrichment_client.get(
        base + "/frames",
        headers=auth_headers,
        params={"from_us": 0, "to_us": end, "snapshot": state["revision"]},
    )
    assert page.status_code == 200, page.text
    assert len(page.json()["frames"]) == 12
    source = enrichment_client.get(
        base + "/source", headers={**auth_headers, "Range": "bytes=0-31"}
    )
    assert source.status_code == 206, source.text
    assert source.content == path.read_bytes()[:32]
    assert enrichment_client.head(base + "/source", headers=auth_headers).status_code == 200
    assert (
        enrichment_client.get(
            base + "/source", headers={**auth_headers, "Range": "bytes=999999999-"}
        ).status_code
        == 416
    )
    while time.monotonic() < deadline:
        state = enrichment_client.get(base, headers=auth_headers).json()
        if state["enrichment"]["status"] in ("complete", "partial", "not_applicable"):
            break
        time.sleep(0.05)
    tracks = enrichment_client.get(
        base + "/tracks", headers=auth_headers, params={"snapshot": state["enrichment"]["revision"]}
    )
    assert tracks.status_code == 200, tracks.text
    assert tracks.json()["items"] and all(x["final"] for x in tracks.json()["items"])
    assert enrichment_client.delete(base, headers=auth_headers).status_code == 204
    assert enrichment_client.delete(base, headers=auth_headers).status_code == 204
    assert enrichment_client.get(base, headers=auth_headers).status_code == 410
    assert enrichment_client.get(base + "/source", headers=auth_headers).status_code == 410
