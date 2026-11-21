"""Lock waits must not occupy the ASGI loop or revive retired requests."""
import asyncio,time
from datetime import UTC,datetime,timedelta
from threading import Event,Thread,Timer,RLock
from types import SimpleNamespace as NS
import cv2,numpy as np,pytest
from app.api.error_handlers import ApiError
from app.domain.models import Detection
from app.domain.schemas import EnrichedVehicleResult
from app.services.image_detection_store import ImageDetectionStore
from app.services.plate_preview_store import PlatePreviewStore
from app.services.plate_preview_service import PlatePreviewService

def scenario():
    expiry=datetime.now(UTC)+timedelta(seconds=30)
    images=ImageDetectionStore(NS(cleanup=lambda now:None),30)
    source=NS(source_id="s",owner_key_id="o",expires_at=expiry,width=40,height=40,detections=(Detection(0,"car",.9,0,0,30,30),))
    images._sources["s"]=source
    ok,png=cv2.imencode(".png",np.indices((40,40)).sum(axis=0).astype(np.uint8))
    def original(*args):
        with images._lock:return png.tobytes(),images.get("s","o")
    images.read_original=original
    item=EnrichedVehicleResult(vehicle_key="detection-1",detection_id=1,class_id=0,class_name="car",attributes_status="completed",plate_status="unreadable",plate={"status":"unreadable","bbox_relative":{"x_min":.1,"y_min":.1,"x_max":.6,"y_max":.6}})
    lock=RLock()
    def job(*args):
        with lock:return NS(status=NS(value="completed"),source_kind="image",source_id="s",expires_at=expiry)
    jobs=NS(get=job,result_by_detection=lambda *a:item,lock=lock)
    store=PlatePreviewStore();service=PlatePreviewService(jobs,images,store)
    return service,store,images,jobs

@pytest.mark.parametrize("held",["image","job","cache"])
def test_lock_wait_does_not_block_loop(held):
    service,store,images,jobs=scenario()
    lock={"image":images._lock,"job":jobs.lock,"cache":store.lock}[held]
    ready=Event();release=Event()
    def holder():
        with lock:ready.set();release.wait(2)
    thread=Thread(target=holder);thread.start();assert ready.wait(1)
    timer=Timer(.25,release.set);timer.start()
    async def exercise():
        start=time.perf_counter()
        async def heartbeat():await asyncio.sleep(.01);return time.perf_counter()-start
        async def disconnected():return False
        request=asyncio.create_task(service.get("s-job",1,"o","r",disconnected))
        tick=asyncio.create_task(heartbeat())
        delay=await tick
        await request
        assert delay<.12
    try:asyncio.run(exercise())
    finally:
        release.set();thread.join();timer.cancel()
        if hasattr(service,"close"):service.close()
        store.close()

def test_expired_access_wait_never_admits_late_compute():
    service,store,images,jobs=scenario();service.request_timeout=.06
    ready=Event();release=Event()
    def holder():
        with store.lock:ready.set();release.wait(2)
    thread=Thread(target=holder);thread.start();ready.wait(1)
    timer=Timer(.25,release.set);timer.start()
    async def exercise():
        async def disconnected():return False
        start=time.perf_counter()
        with pytest.raises(ApiError) as exc:await service.get("j",1,"o","r",disconnected)
        assert exc.value.status_code==504
        assert time.perf_counter()-start<.2
    try:asyncio.run(exercise())
    finally:
        release.set();thread.join();timer.cancel()
        if hasattr(service,"close"):service.close()
        store.close()
    assert not store.busy and store.entry_count==0

def test_disconnect_during_access_retires_without_late_publication():
 service,store,images,jobs=scenario()
 ready=Event();release=Event()
 def holder():
  with jobs.lock:ready.set();release.wait(2)
 thread=Thread(target=holder);thread.start();assert ready.wait(1)
 async def exercise():
  start=time.perf_counter()
  async def disconnected():return time.perf_counter()-start>=.03
  with pytest.raises(ApiError) as exc:await service.get("j",1,"o","r",disconnected)
  assert exc.value.status_code==503 and time.perf_counter()-start<.15
 try:asyncio.run(exercise())
 finally:release.set();thread.join();service.close();store.close()
 assert store.entry_count==0 and not store.busy

def test_access_workers_have_no_unbounded_queue():
 service,store,images,jobs=scenario();service.request_timeout=.06
 ready=Event();release=Event()
 def holder():
  with jobs.lock:ready.set();release.wait(2)
 thread=Thread(target=holder);thread.start();ready.wait(1)
 async def exercise():
  async def disconnected():return False
  async def request():
   try:await service.get("j",1,"o","r",disconnected);return 200
   except ApiError as exc:return exc.status_code
  return await asyncio.gather(*(request() for _ in range(5)))
 try:
  statuses=asyncio.run(exercise())
  assert statuses.count(429)==1 and statuses.count(504)==4
 finally:
  release.set();thread.join();service.close();store.close()
 assert store.entry_count==0

def test_retirement_does_not_wait_for_a_blocked_cache():
 from app.services.plate_preview_store import PreviewValue
 service,store,images,jobs=scenario();expiry=datetime.now(UTC)+timedelta(seconds=30)
 gate=Event();started=Event();ready=Event();release=Event()
 def compute(check):started.set();gate.wait(2);check();return PreviewValue(b"png","{}",expiry)
 consumer=store.acquire((1,),expiry,compute,lambda:None);assert started.wait(1)
 def holder():
  with store.lock:ready.set();release.wait(2)
 thread=Thread(target=holder);thread.start();ready.wait(1)
 timer=Timer(.3,release.set);timer.start()
 try:
  start=time.perf_counter();store.release(consumer)
  assert time.perf_counter()-start<.1
  gate.set()
  with pytest.raises(ApiError):consumer.future.result(1)
  assert store.entry_count==0
 finally:release.set();gate.set();thread.join();timer.cancel();service.close();store.close()
