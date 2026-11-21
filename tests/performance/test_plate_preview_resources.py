import time,logging
from datetime import UTC,datetime,timedelta
import psutil
from app.services.plate_preview_store import PlatePreviewStore,PreviewValue
from app.services.temporary_cleanup import PeriodicCleanup
def test_actual_janitor_purges_without_traffic_and_cache_stays_bounded(record_property):
    store=PlatePreviewStore();janitor=PeriodicCleanup((store,),logging.getLogger("preview-resources"))
    from app.services.inference_metrics import InferenceMetrics
    observation=InferenceMetrics(logging.getLogger("preview-resources"),"plate_preview_resources").__enter__()
    initial=psutil.Process().memory_info().rss
    janitor.start()
    try:
        expiry=datetime.now(UTC)+timedelta(seconds=.3)
        for n in range(30):
            token=store.acquire((n,),expiry,lambda check:PreviewValue(b"x"*100000,"{}",expiry),lambda:None)
            token.future.result(1);store.release(token)
            assert store.entry_count<=8 and store.byte_count<=16*1024*1024
        start=time.perf_counter()
        while store.entry_count and time.perf_counter()-start<2:time.sleep(.02)
        elapsed=time.perf_counter()-start
        assert store.entry_count==0 and elapsed<=2
        record_property("purge_seconds",round(elapsed,4))
        final=psutil.Process().memory_info().rss
        assert final-initial<32*1024*1024
    finally:
        janitor.close();store.close();observation.__exit__(None,None,None)
        record_property("rss_initial_mb",round(observation.initial_memory_mb,2))
        record_property("rss_peak_mb",round(observation._peak,2))
        record_property("rss_final_mb",round(psutil.Process().memory_info().rss/1024/1024,2))
