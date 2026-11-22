import time,logging
from datetime import UTC,datetime,timedelta
from threading import Event
import pytest
from app.api.error_handlers import ApiError
from app.services.plate_preview_store import PlatePreviewStore,PreviewValue
from app.services.inference_metrics import InferenceMetrics
@pytest.mark.parametrize("stage",["factory","enter","exit"])
def test_instrumentation_failure_resolves_request_and_releases_slot(stage):
    expiry=datetime.now(UTC)+timedelta(seconds=30);store=PlatePreviewStore()
    class Metric:
        status="completed";error_code=None
        def __enter__(self):
            if stage=="enter":raise RuntimeError("PRIVATE_CANARY")
            return self
        def __exit__(self,*args):
            if stage=="exit":raise RuntimeError("PRIVATE_CANARY")
    def factory():
        if stage=="factory":raise RuntimeError("PRIVATE_CANARY")
        return Metric()
    consumer=store.acquire((1,),expiry,lambda check:PreviewValue(b"png","{}",expiry),lambda:None,measure=factory)
    try:
        with pytest.raises(ApiError) as exc:consumer.future.result(.5)
        assert exc.value.status_code==503 and "PRIVATE" not in exc.value.message
        for _ in range(100):
            if not store.busy:break
            time.sleep(.002)
        assert not store.busy and store.entry_count==0
        next_consumer=store.acquire((2,),expiry,lambda check:PreviewValue(b"png","{}",expiry),lambda:None)
        assert next_consumer.future.result(1).png==b"png"
    finally:store.close()

def test_partial_sampler_start_is_cleaned(monkeypatch):
    metric=InferenceMetrics(logging.getLogger("partial"),"plate_preview")
    def broken_start(*args):raise RuntimeError("synthetic")
    monkeypatch.setattr("app.services.inference_metrics.threading.Thread.start",broken_start)
    with pytest.raises(RuntimeError):metric.__enter__()
    assert metric._stop.is_set()

@pytest.mark.parametrize("stage",["initial_sample","final_sample"])
def test_real_sampler_failure_never_caches_evidence(stage,monkeypatch):
 expiry=datetime.now(UTC)+timedelta(seconds=30);store=PlatePreviewStore()
 metric=InferenceMetrics(logging.getLogger("sampler-failure"),"plate_preview",defer_emit=True)
 original=metric._sample;calls=[]
 def sample():
  calls.append(1)
  if stage=="initial_sample" or len(calls)>1:raise RuntimeError("PRIVATE_CANARY")
  return original()
 monkeypatch.setattr(metric,"_sample",sample)
 c=store.acquire((1,),expiry,lambda check:PreviewValue(b"png","{}",expiry),lambda:None,measure=lambda:metric)
 try:
  with pytest.raises(ApiError):c.future.result(1)
  for _ in range(100):
   if not store.busy:break
   time.sleep(.002)
  assert not store.busy and store.entry_count==0 and metric._stop.is_set()
 finally:store.close()
