import time
from tests.fixtures_progressive import video


def test_evidence_budget_and_legacy_cache_reuse(
    enrichment_client, tmp_path, auth_headers, monkeypatch
):
    client = enrichment_client
    processor = client.app.state.enrichment_job_service.processor
    original = processor.enrich
    calls = []

    def counted(*a, **kw):
        calls.append(a[1])
        return original(*a, **kw)

    monkeypatch.setattr(processor, "enrich", counted)
    path = video(tmp_path / "sample.mp4")
    receipt = client.post(
        "/api/v1/video-jobs?presentation=progressive",
        headers=auth_headers,
        files={"video": ("clip.mp4", path.read_bytes(), "video/mp4")},
    )
    assert receipt.status_code == 202, receipt.text
    job = receipt.json()["job_id"]
    base = f"/api/v1/video-jobs/{job}"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        state = client.get(base + "/playback", headers=auth_headers).json()
        if (
            state["enrichment"]["source_closed"]
            and state["enrichment"]["terminal_units"] == state["enrichment"]["discovered_units"]
            and client.get(base, headers=auth_headers).json()["status"] == "completed"
        ):
            break
        time.sleep(0.025)
    assert state["enrichment"]["terminal_units"] == 1
    assert 1 <= len(calls) <= 4 and len(set(calls)) == len(calls)
    store = client.app.state.progressive_store
    with store.lock:
        records = store.db.execute(
            "SELECT idx,candidate,provisional,result,path FROM p_evidence WHERE job=? ORDER BY idx",
            (job,),
        ).fetchall()
    assert sum(r["candidate"] for r in records) == 3
    unit = client.app.state.progressive_evidence.track(job, store.row(job)["owner"], 1)
    assert unit["final"] and [e["frame_index"] for e in unit["evidence"]] == [0, 1, 2]
    # Raw crop is solid; painting happened only after this capture.
    import cv2, numpy as np

    crop = cv2.imdecode(
        np.frombuffer(__import__("pathlib").Path(records[0]["path"]).read_bytes(), np.uint8),
        cv2.IMREAD_COLOR,
    )
    assert np.unique(crop.reshape(-1, 3), axis=0).shape[0] == 1
    before = len(calls)
    accepted = client.post(
        "/api/v1/enrichment-jobs",
        headers=auth_headers,
        json={"source": {"kind": "video", "source_id": job}},
    )
    assert accepted.status_code == 202, accepted.text
    enrichment = accepted.json()["enrichment_job_id"]
    while time.monotonic() < deadline:
        result = client.get("/api/v1/enrichment-jobs/" + enrichment, headers=auth_headers).json()
        if result["status"] == "completed":
            break
        time.sleep(0.025)
    assert result["status"] == "completed"
    assert len(calls) == before
    for _ in range(5):
        assert client.get(base + "/playback/tracks/1", headers=auth_headers).status_code == 200
    assert len(calls) == before
