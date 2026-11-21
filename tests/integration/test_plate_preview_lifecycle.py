import asyncio,json,time
from dataclasses import replace
from datetime import UTC,datetime,timedelta
from threading import Event,Thread
from unittest.mock import Mock
import pytest
from app.api.error_handlers import ApiError
from tests.integration.test_plate_preview_access import completed
def test_foreign_detection_no_bbox_non_image_and_cache_reauthorization(enrichment_client,auth_headers):
    c=enrichment_client;source,jid=completed(c,auth_headers)
    service=c.app.state.plate_preview_service;jobs=c.app.state.enrichment_jobs;images=c.app.state.image_sources
    owner=next(iter(images._sources.values())).owner_key_id
    with pytest.raises(ApiError) as foreign:service.resolve(jid,1,"foreign")
    assert foreign.value.status_code==404
    url=f"/api/v1/enrichment-jobs/{jid}/detections/1/plate-preview"
    first=c.get(url,headers=auth_headers);assert first.status_code==200
    assert "X-Plate-Preview-Metadata" in c.get(url,headers={**auth_headers,"Origin":"http://localhost:5173"}).headers.get("access-control-expose-headers","")
    with jobs.lock,jobs.connection:
        row=jobs.connection.execute("SELECT results_json FROM enrichment_jobs WHERE enrichment_job_id=?",(jid,)).fetchone()
        data=json.loads(row[0]);data[0]["plate"]["status"]="not_detected";data[0]["plate_status"]="not_detected";data[0]["plate"].pop("bbox_relative",None)
        jobs.connection.execute("UPDATE enrichment_jobs SET results_json=? WHERE enrichment_job_id=?",(json.dumps(data),jid))
    assert c.get(url,headers=auth_headers).status_code==422
    with jobs.lock,jobs.connection:jobs.connection.execute("UPDATE enrichment_jobs SET source_kind='video' WHERE enrichment_job_id=?",(jid,))
    assert c.get(url,headers=auth_headers).status_code==409
    assert c.get(url+"?bbox=private",headers=auth_headers).status_code==422
def test_health_remains_responsive_and_expiry_prevents_publication(enrichment_client,auth_headers,monkeypatch):
    c=enrichment_client;source,jid=completed(c,auth_headers)
    started=Event();release=Event();out=[]
    import app.services.plate_preview_service as module
    actual=module.display_contrast
    def blocked(crop):started.set();release.wait(3);return actual(crop)
    monkeypatch.setattr(module,"display_contrast",blocked)
    url=f"/api/v1/enrichment-jobs/{jid}/detections/1/plate-preview"
    thread=Thread(target=lambda:out.append(c.get(url,headers=auth_headers)));thread.start()
    assert started.wait(2)
    start=time.perf_counter();assert c.get("/health/live").status_code==200;assert time.perf_counter()-start<1
    images=c.app.state.image_sources
    with images._lock:
        original=images._sources[source["request_id"]]
        images._sources[source["request_id"]]=replace(original,expires_at=datetime.now(UTC)-timedelta(seconds=1))
    release.set();thread.join(4)
    assert not thread.is_alive() and out[0].status_code==410
    assert c.app.state.plate_preview_store.entry_count==0

def test_all_disconnected_consumers_cannot_publish_and_keep_permit(enrichment_client,auth_headers,monkeypatch):
 c=enrichment_client;source,jid=completed(c,auth_headers)
 service=c.app.state.plate_preview_service;store=c.app.state.plate_preview_store
 owner=next(iter(c.app.state.image_sources._sources.values())).owner_key_id
 gate=Event();started=Event()
 import app.services.plate_preview_service as module
 original=module.display_contrast
 def blocked(image):started.set();gate.wait(2);return original(image)
 monkeypatch.setattr(module,"display_contrast",blocked)
 async def disconnected():return True
 with pytest.raises(ApiError):asyncio.run(service.get(jid,1,owner,"request",disconnected))
 gate.set()
 for _ in range(100):
  if not store.busy:break
  time.sleep(.01)
 assert store.entry_count==0 and not store.busy
