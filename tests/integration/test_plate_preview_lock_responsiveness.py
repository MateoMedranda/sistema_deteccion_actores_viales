"""Real HTTP health and SQLite/image/cache lock waits share an ASGI loop."""
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event,Timer
import pytest
from tests.integration.test_plate_preview_access import completed

@pytest.mark.parametrize("held",["image","sqlite","cache"])
def test_health_served_while_access_waits(enrichment_client,auth_headers,held,record_property):
    client=enrichment_client
    source,job=completed(client,auth_headers)
    state=client.app.state
    lock={"image":state.image_sources._lock,"sqlite":state.enrichment_jobs.lock,"cache":state.plate_preview_store.lock}[held]
    entered=Event()
    resolve=state.plate_preview_service.resolve
    def observed(*args):
        entered.set()
        return resolve(*args)
    state.plate_preview_service.resolve=observed
    with ThreadPoolExecutor(max_workers=1) as pool:
        held_ready=Event();release=Event()
        def owner():
            with lock:
                held_ready.set();release.wait(2)
        from threading import Thread
        owner_thread=Thread(target=owner);owner_thread.start()
        assert held_ready.wait(1)
        timer=Timer(.4,release.set);timer.start()
        try:
            request=pool.submit(client.get,f"/api/v1/enrichment-jobs/{job}/detections/1/plate-preview",headers=auth_headers)
            assert entered.wait(1)
            start=time.perf_counter()
            response=client.get("/health/live")
            elapsed=time.perf_counter()-start
            assert response.status_code==200
            assert elapsed<.2
            assert not release.is_set()
            record_property("health_seconds_"+held,round(elapsed,4))
            release.set()
            assert request.result(2).status_code==200
        finally:
            release.set();owner_thread.join();timer.cancel()
