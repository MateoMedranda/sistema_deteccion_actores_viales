import json
import time
import av
from tests.integration.test_video_profile_pipeline import submit, report


def wait_export(client, job, headers):
    deadline=time.monotonic()+15
    while time.monotonic()<deadline:
        result=client.get(f"/api/v1/video-jobs/{job}/playback/export",headers=headers)
        assert result.status_code==200,result.text
        if result.json()["state"] in ("ready","failed"):return result.json()
        time.sleep(.025)
    raise AssertionError("Export did not finish")


def test_analysis_does_not_generate_video_and_explicit_export_reuses_annotations(enrichment_client,tmp_path,auth_headers,monkeypatch):
    client=enrichment_client
    job=submit(client,tmp_path,auth_headers)
    _,profile=report(client,job)
    assert profile["outcome"]=="completed"
    assert all(profile["stages"][key]["calls"]==0 for key in ("annotation","video_write","final_encode"))
    parent=client.app.state.video_jobs.get(job,"default")
    assert parent.output_path is None
    assert not list(client.app.state.video_artifacts.output_root.iterdir())
    base=f"/api/v1/video-jobs/{job}"
    assert client.get(base+"/playback/export",headers=auth_headers).json()["state"]=="waiting"
    assert client.get(base+"/annotated-video",headers=auth_headers).status_code==409
    def no_inference(*args,**kwargs):raise AssertionError("Export must never call YOLO")
    monkeypatch.setattr(client.app.state.video_worker.processor.detector,"detect",no_inference)
    assert client.post(base+"/playback/export",headers=auth_headers).status_code==202
    result=wait_export(client,job,auth_headers)
    assert result["state"]=="ready" and result["processed_frames"]==12
    artifact=client.get(result["url"],headers={**auth_headers,"Range":"bytes=0-31"})
    assert artifact.status_code==206
    output=client.app.state.video_jobs.get(job,"default").output_path
    with av.open(str(output)) as container:
        assert container.streams.video[0].codec_context.name=="h264"
        assert sum(1 for _ in container.decode(video=0))==12
    assert client.post(base+"/playback/export",headers=auth_headers).json()["state"]=="ready"
    assert client.app.state.video_jobs.get(job,"default").output_path==output
    assert client.get(base+"/playback",headers=auth_headers).json()["analysis_state"]=="complete"


def test_export_failure_is_separate_retryable_and_does_not_fail_analysis(enrichment_client,tmp_path,auth_headers,monkeypatch):
    client=enrichment_client
    job=submit(client,tmp_path,auth_headers)
    report(client,job)
    exporter=client.app.state.progressive_export
    original=exporter.encoder
    def fail(*args,**kwargs):raise RuntimeError("PRIVATE_PATH_AND_PLATE")
    monkeypatch.setattr(exporter,"encoder",fail)
    base=f"/api/v1/video-jobs/{job}/playback"
    client.post(base+"/export",headers=auth_headers)
    result=wait_export(client,job,auth_headers)
    assert result["state"]=="failed" and result["error_code"]=="export_failed"
    assert "PRIVATE_PATH" not in json.dumps(result)
    assert client.get(base,headers=auth_headers).json()["analysis_state"]=="complete"
    assert client.app.state.video_jobs.get(job,"default").status.value=="completed"
    monkeypatch.setattr(exporter,"encoder",original)
    assert client.post(base+"/export",headers=auth_headers).status_code==202
    assert wait_export(client,job,auth_headers)["state"]=="ready"


def test_export_post_is_idempotent_and_owner_query_body_are_checked(enrichment_client,tmp_path,auth_headers,monkeypatch):
    client=enrichment_client
    job=submit(client,tmp_path,auth_headers)
    report(client,job)
    exporter=client.app.state.progressive_export
    monkeypatch.setattr(exporter,"claim",lambda:None)
    base=f"/api/v1/video-jobs/{job}/playback/export"
    assert client.get(base).status_code==401
    client.app.state.settings.api_keys="other:other-key"
    assert client.post(base,headers={"X-API-Key":"other-key"}).status_code==404
    assert client.post(base+"?url=evil",headers=auth_headers).status_code==422
    assert client.post(base,headers=auth_headers,json={"url":"evil"}).status_code==422
    for _ in range(3):assert client.post(base,headers=auth_headers).json()["state"]=="queued"
    store=client.app.state.progressive_store
    with store.lock:assert store.db.execute("SELECT count(*) FROM p_video_exports WHERE job=?",(job,)).fetchone()[0]==1
    client.delete(f"/api/v1/video-jobs/{job}/playback",headers=auth_headers)
    assert client.get(base,headers=auth_headers).status_code==410


def test_withdraw_during_export_never_publishes_the_file(enrichment_client,tmp_path,auth_headers,monkeypatch):
    client=enrichment_client
    job=submit(client,tmp_path,auth_headers)
    report(client,job)
    exporter=client.app.state.progressive_export
    def withdraw(source,destination,*args):
        destination.write_bytes(b"not published")
        exporter.store.withdraw(job,"default")
    monkeypatch.setattr(exporter,"encoder",withdraw)
    assert client.post(f"/api/v1/video-jobs/{job}/playback/export",headers=auth_headers).status_code==202
    end=time.monotonic()+10
    while time.monotonic()<end:
        if client.get(f"/api/v1/video-jobs/{job}/playback",headers=auth_headers).status_code==410 and not exporter.store.readers:break
        time.sleep(.02)
    assert client.get(f"/api/v1/video-jobs/{job}/annotated-video/content",headers=auth_headers).status_code==410
    assert not list(client.app.state.video_artifacts.output_root.iterdir())


def test_export_is_not_available_for_incomplete_analysis(enrichment_client,tmp_path,auth_headers):
    client=enrichment_client
    job=submit(client,tmp_path,auth_headers)
    report(client,job)
    store=client.app.state.progressive_store
    with store.lock,store.db:
        store.db.execute("UPDATE p_video SET analysis='partial_failed' WHERE job=?",(job,))
    assert client.post(f"/api/v1/video-jobs/{job}/playback/export",headers=auth_headers).status_code==409
    assert not list(client.app.state.video_artifacts.output_root.iterdir())


def test_missing_cached_export_is_regenerated_without_exposing_partial_output(enrichment_client,tmp_path,auth_headers,monkeypatch):
    client=enrichment_client
    job=submit(client,tmp_path,auth_headers)
    report(client,job)
    url=f"/api/v1/video-jobs/{job}/playback/export"
    client.post(url,headers=auth_headers)
    assert wait_export(client,job,auth_headers)["state"]=="ready"
    output=client.app.state.video_jobs.get(job,"default").output_path
    output.unlink()
    exporter=client.app.state.progressive_export
    monkeypatch.setattr(exporter,"claim",lambda:None)
    assert client.get(url,headers=auth_headers).json()["state"]=="waiting"
    assert client.post(url,headers=auth_headers).json()["state"]=="queued"
    assert client.app.state.video_jobs.get(job,"default").output_path is None
    assert client.get(f"/api/v1/video-jobs/{job}/annotated-video/content",headers=auth_headers).status_code==404


def test_explicit_legacy_count_output_can_request_its_required_base_export(enrichment_client,tmp_path,auth_headers):
    client=enrichment_client
    job=submit(client,tmp_path,auth_headers)
    report(client,job)
    line=dict(point_a=dict(x=0,y=.5),point_b=dict(x=1,y=.5))
    response=client.post(f"/api/v1/video-jobs/{job}/count-jobs",headers=auth_headers,json=line)
    assert response.status_code==202,response.text
    count_id=response.json()["count_job_id"]
    end=time.monotonic()+15
    while time.monotonic()<end:
        state=client.get(f"/api/v1/count-jobs/{count_id}",headers=auth_headers).json()
        if state["status"] in ("completed","failed"):break
        time.sleep(.025)
    assert state["status"]=="completed",state
    assert client.get(f"/api/v1/video-jobs/{job}/playback/export",headers=auth_headers).json()["state"]=="ready"


def test_interrupted_export_recovery_does_not_change_complete_analysis(enrichment_client,tmp_path,auth_headers):
    from app.services.progressive_export import ProgressiveExport
    client=enrichment_client
    job=submit(client,tmp_path,auth_headers)
    report(client,job)
    store=client.app.state.progressive_store
    output=client.app.state.video_artifacts.annotated_output_path()
    raw=output.with_suffix(".raw.mp4")
    output.write_bytes(b"partial");raw.write_bytes(b"partial")
    with store.lock,store.db:
        store.db.execute("INSERT INTO p_video_exports VALUES(?,'encoding',12,NULL,?,?)",(job,str(output),str(raw)))
        store.db.execute("UPDATE p_video SET export='encoding' WHERE job=?",(job,))
    recovered=ProgressiveExport(store,client.app.state.video_jobs,client.app.state.video_artifacts,client.app.state.settings,client.app.state.video_worker.processor.logger)
    assert recovered.status(job,"default")["state"]=="failed"
    assert recovered.status(job,"default")["error_code"]=="export_interrupted"
    assert not output.exists() and not raw.exists()
    assert client.get(f"/api/v1/video-jobs/{job}/playback",headers=auth_headers).json()["analysis_state"]=="complete"


def test_export_contract_and_expiry_cleanup(enrichment_client,tmp_path,auth_headers):
    import jsonschema
    from pathlib import Path
    client=enrichment_client
    job=submit(client,tmp_path,auth_headers)
    report(client,job)
    url=f"/api/v1/video-jobs/{job}/playback/export"
    receipt=client.post(url,headers=auth_headers)
    definitions=json.loads((Path(__file__).resolve().parents[3]/"specs/009-video-progresivo/contracts/schemas.json").read_text())["$defs"]
    jsonschema.validate(receipt.json(),{"$ref":"#/$defs/VideoExportStatus","$defs":definitions})
    assert wait_export(client,job,auth_headers)["state"]=="ready"
    output=client.app.state.video_jobs.get(job,"default").output_path
    store=client.app.state.progressive_store
    with store.lock,store.db:
        store.db.execute("UPDATE p_video SET expires='2000-01-01T00:00:00+00:00' WHERE job=?",(job,))
    assert client.get(url,headers=auth_headers).status_code==410
    store.cleanup()
    assert not output.exists()
    with store.lock:
        assert not store.db.execute("SELECT 1 FROM p_video_exports WHERE job=?",(job,)).fetchone()
