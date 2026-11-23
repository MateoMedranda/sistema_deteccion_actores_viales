import logging,time
from tests.fixtures_progressive import video

def test_progressive_pipeline_measures_frames_and_memory(enrichment_client,tmp_path,auth_headers,monkeypatch):
    records=[];original=logging.Logger.info
    def info(logger,msg,*args,**kwargs):
        if msg in ("video_frame_processed","progressive_video_outcome"):records.append((msg,kwargs.get("extra",{})))
        return original(logger,msg,*args,**kwargs)
    monkeypatch.setattr(logging.Logger,"info",info)
    source=video(tmp_path/"sample.mp4")
    receipt=enrichment_client.post("/api/v1/video-jobs?presentation=progressive&enrichment=on-demand",headers=auth_headers,files={"video":("sample.mp4",source.read_bytes(),"video/mp4")}).json()
    end=time.monotonic()+10
    while time.monotonic()<end:
        if any(msg=="progressive_video_outcome" for msg,_ in records):break
        time.sleep(.02)
    frames=[fields for msg,fields in records if msg=="video_frame_processed"]
    assert len(frames)==12
    assert all(f["job_id"]==receipt["job_id"] and f["frame_ms"]>=0 and f["memory_mb"]>0 for f in frames)
    assert all("path" not in f and "plate" not in f for _,f in records)


def test_validation_failure_keeps_safe_diagnostic_without_exception_text(enrichment_client,tmp_path,auth_headers,monkeypatch):
    records=[];original=logging.Logger.error
    def error(logger,msg,*args,**kwargs):
        if msg=="progressive_processing_failed":records.append(kwargs.get("extra",{}))
        return original(logger,msg,*args,**kwargs)
    monkeypatch.setattr(logging.Logger,"error",error)
    def reject(*args,**kwargs):raise ValueError("invalid_observation")
    monkeypatch.setattr(enrichment_client.app.state.progressive_store,"publish",reject)
    source=video(tmp_path/"sample.mp4")
    receipt=enrichment_client.post("/api/v1/video-jobs?presentation=progressive&enrichment=on-demand",headers=auth_headers,files={"video":("sample.mp4",source.read_bytes(),"video/mp4")}).json()
    end=time.monotonic()+10
    while time.monotonic()<end:
        state=enrichment_client.get("/api/v1/video-jobs/"+receipt["job_id"],headers=auth_headers).json()
        if state["status"]=="failed":break
        time.sleep(.02)
    assert state["status"]=="failed"
    assert records and records[0]["error_code"]=="invalid_observation" and records[0]["exception_type"]=="ValueError"
    assert all(str(tmp_path) not in str(r) and "exception_message" not in r for r in records)
