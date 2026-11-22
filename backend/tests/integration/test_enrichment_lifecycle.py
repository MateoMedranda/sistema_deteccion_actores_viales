from dataclasses import replace
from datetime import UTC, datetime, timedelta
import logging
import time
from app.services.temporary_cleanup import PeriodicCleanup
from tests.conftest import image_bytes

def test_background_cleanup_purges_original_without_any_new_request(client,auth_headers):
    response=client.post("/api/v1/detections/images",headers=auth_headers,
        files={"image":("scene.jpg",image_bytes(),"image/jpeg")}).json()
    source_id=response["request_id"]
    sources=client.app.state.image_sources
    source=sources._sources[source_id]
    with sources._lock:
        sources._sources[source_id]=replace(source,expires_at=datetime.now(UTC)-timedelta(seconds=1))
    deadline=time.monotonic()+2
    while source.original_path.exists() and time.monotonic()<deadline:
        time.sleep(.01)
    assert not source.original_path.exists()
    assert client.get(response["original_image"]["url"],headers=auth_headers).status_code==410

def test_cleanup_closes_and_continues_after_independent_failure():
    calls=[]
    class Broken:
        def cleanup(self): raise RuntimeError("PRIVATE_PATH")
    class Healthy:
        def cleanup(self): calls.append("clean")
    janitor=PeriodicCleanup((Broken(),Healthy()),logging.getLogger("test.cleanup"),interval=.01)
    janitor.run_once()
    assert calls==["clean"]
    janitor.start(); janitor.close()
    assert not janitor.thread.is_alive()

def test_restarted_store_janitor_purges_orphans_without_requests(tmp_path):
    from app.services.source_artifacts import SourceArtifactStore
    from app.services.image_detection_store import ImageDetectionStore
    now=datetime.now(UTC)
    source=ImageDetectionStore(SourceArtifactStore(tmp_path),1,clock=lambda:now).create("source","owner",b"pixels","image/png",1,1,[])
    foreign=tmp_path/"foreign.jpg";foreign.write_bytes(b"keep")
    restarted=ImageDetectionStore(SourceArtifactStore(tmp_path),1,clock=lambda:now+timedelta(seconds=2))
    janitor=PeriodicCleanup((restarted,),logging.getLogger("test.restart"),interval=.01)
    janitor.start()
    try:
        deadline=time.monotonic()+2
        while source.original_path.exists() and time.monotonic()<deadline:time.sleep(.01)
        assert not source.original_path.exists()
        assert foreign.read_bytes()==b"keep"
    finally:janitor.close()
