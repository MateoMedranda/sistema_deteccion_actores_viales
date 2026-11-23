from datetime import UTC, datetime, timedelta
from fractions import Fraction
from types import SimpleNamespace
import json, logging
import numpy as np
import pytest
from app.adapters.timed_video_decoder import TimedFrame
from app.domain.models import Detection
from app.services.progressive_evidence import ProgressiveEvidence
from app.services.progressive_enrichment import ProgressiveEnrichment
from app.services.video_progressive_store import ProgressiveStore
from app.services.progressive_counting import ProgressiveCountService
from app.api.error_handlers import ApiError


def setup(tmp_path):
    store = ProgressiveStore(tmp_path / "db")
    source = tmp_path / "source"; source.write_bytes(b"private")
    store.create("job", "owner", source, dict(width=100,height=100,duration=10), datetime.now(UTC)+timedelta(minutes=5), on_demand=True)
    evidence = ProgressiveEvidence(store,tmp_path/"crops",{"car"},3); evidence.initialize()
    return store,evidence


def publish(store,evidence,index,y):
    frame=TimedFrame(index,index,Fraction(1,10),index*100000,(index+1)*100000,np.zeros((100,100,3),np.uint8))
    pairs=[(Detection(0,"car",.9,10,y,30,y+10),1),(Detection(0,"car",.8,50,10,70,30),2)]
    prepared=evidence.prepare(SimpleNamespace(job_id="job"),frame,pairs)
    obs=[dict(track_id=tid,class_id=d.class_id,class_name=d.class_name,confidence=d.confidence,raw_bbox=dict(x_min=d.x_min,y_min=d.y_min,x_max=d.x_max,y_max=d.y_max),display_bbox=None) for d,tid in pairs]
    frames=[dict(frame_index=index,start_us=frame.start_us,end_us=frame.end_us,pts=str(index),observations=obs)]
    store.publish("job",frames,on_publish=lambda:evidence.commit(SimpleNamespace(job_id="job"),prepared,frames))


def test_only_selected_track_is_enriched_and_repeated_selection_reuses_result(tmp_path):
    store,evidence=setup(tmp_path); calls=[]
    class Processor:
        accept_threshold=.8
        def enrich(self,image,index,**kwargs):
            calls.append(index)
            return dict(status="completed",items=[]),dict(status="not_detected",used_enhancement=False)
    worker=ProgressiveEnrichment(evidence,Processor(),logging.getLogger("test"))
    publish(store,evidence,0,10)
    assert worker.claim() is None
    assert evidence.track("job","owner",1)["state"]=="not_requested"
    receipt=evidence.request("job","owner",1)
    assert receipt["evidence"] and receipt["evidence"][0]["vehicle_url"]
    while (rec:=worker.claim()) is not None:
        assert rec["track"]==1
        worker.evaluate(rec);worker.dirty.add("job");worker.refresh()
    assert len(calls)==1
    assert evidence.track("job","owner",1)["final"]
    assert evidence.track("job","owner",2)["state"]=="not_requested"
    publish(store,evidence,1,70)
    evidence.request("job","owner",1)
    assert worker.claim() is None and len(calls)==1
    with pytest.raises(ApiError):evidence.request("job","intruder",2)
    store.withdraw("job","owner")
    with pytest.raises(ApiError):evidence.request("job","owner",1)
    store.close()


def test_count_uses_published_tracks_and_rewinding_never_duplicates(tmp_path):
    store,evidence=setup(tmp_path)
    publish(store,evidence,0,10); publish(store,evidence,1,70)
    service=ProgressiveCountService(store)
    line=dict(point_a=dict(x=0,y=.5),point_b=dict(x=1,y=.5))
    result=service.configure("job","owner",line)
    assert result["total"]==1
    assert service.configure("job","owner",line)["revision"]==result["revision"]
    assert service.snapshot("job","owner",0)["total"]==0
    assert service.snapshot("job","owner",100000)["total"]==1
    publish(store,evidence,2,10)
    assert service.snapshot("job","owner",200000)["total"]==1
    assert service.snapshot("job","owner",0)["total"]==0
    assert service.snapshot("job","owner",200000)["total"]==1
    with pytest.raises(ApiError):service.snapshot("job","intruder",0)
    with pytest.raises(ApiError):service.snapshot("job","owner",99999999)
    with pytest.raises(ApiError):service.configure("job","owner",dict(point_a=dict(x=0,y=0),point_b=dict(x=0,y=0)))
    changed=service.configure("job","owner",dict(point_a=dict(x=.9,y=0),point_b=dict(x=.9,y=1)))
    assert changed["revision"]>result["revision"] and changed["total"]==0
    assert service.configure("job","owner",line)["total"]==1
    service.disable("job","owner")
    assert not service.snapshot("job","owner",0)["enabled"]
    service.configure("job","owner",line)
    store.withdraw("job","owner")
    with pytest.raises(ApiError):service.snapshot("job","owner",0)
    store.close()


def test_on_demand_api_and_count_routes(enrichment_client,tmp_path,auth_headers,monkeypatch):
    import time
    from tests.fixtures_progressive import video
    calls=[]
    processor=enrichment_client.app.state.progressive_worker.processor
    original=processor.enrich
    def observed(*args,**kwargs):
        calls.append(kwargs.get("job_id"))
        return original(*args,**kwargs)
    monkeypatch.setattr(processor,"enrich",observed)
    sample=video(tmp_path/"sample.mp4")
    body=lambda:{"video":("sample.mp4",sample.read_bytes(),"video/mp4")}
    response=enrichment_client.post("/api/v1/video-jobs?presentation=progressive&enrichment=on-demand",headers=auth_headers,files=body())
    assert response.status_code==202,response.text
    job=response.json()["job_id"];base=f"/api/v1/video-jobs/{job}/playback"
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        state=enrichment_client.get(base,headers=auth_headers).json()
        if state["analysis_state"]=="complete":break
        time.sleep(.02)
    assert state["analysis_state"]=="complete" and calls==[]
    tracks=enrichment_client.get(base+"/tracks",params={"snapshot":state["enrichment"]["revision"]},headers=auth_headers).json()["items"]
    assert tracks and all(t["state"]=="not_requested" for t in tracks)
    tid=tracks[0]["track_id"]
    assert enrichment_client.post(base+f"/tracks/{tid}/enrich",headers=auth_headers).status_code==202
    while time.monotonic()<deadline:
        track=enrichment_client.get(base+f"/tracks/{tid}",headers=auth_headers).json()
        if track["final"]:break
        time.sleep(.02)
    assert track["final"] and 1<=len(calls)<=3
    n=len(calls)
    assert enrichment_client.post(base+f"/tracks/{tid}/enrich",headers=auth_headers).status_code==202
    assert len(calls)==n
    line=dict(point_a=dict(x=0,y=.5),point_b=dict(x=1,y=.5))
    assert enrichment_client.put(base+"/count",json=line,headers=auth_headers).status_code==200
    count=enrichment_client.get(base+"/count?at_us=0",headers=auth_headers)
    assert count.status_code==200 and count.json()["enabled"]
    assert enrichment_client.get(base+"/count?at_us=0&at_us=1",headers=auth_headers).status_code==422
    assert enrichment_client.delete(base+"/count",headers=auth_headers).status_code==204
    assert not enrichment_client.get(base+"/count?at_us=0",headers=auth_headers).json()["enabled"]
    assert enrichment_client.post("/api/v1/video-jobs?enrichment=on-demand",headers=auth_headers,files=body()).status_code==422
