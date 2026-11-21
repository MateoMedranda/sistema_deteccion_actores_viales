"""Safe process-RSS observations; memory is not exclusive allocation per job."""
import logging
import re
import threading
from time import perf_counter
import psutil

class InferenceMetrics:
    def __init__(self, logger: logging.Logger, branch: str, *, request_id=None, job_id=None, source_type="image", profile_id=None, defer_emit=False):
        self.logger,self.branch=logger,branch
        self.request_id,self.job_id,self.source_type=request_id,job_id,source_type
        self.profile_id=profile_id if profile_id=="display-contrast-v1" else None
        self.status,self.error_code="completed",None
        self._stop=threading.Event()
        self._peak=0.0
        self._sampler=None
        self._sampling_error=False
        self._defer_emit=defer_emit
        self._ready=False
        self._published=False

    def defer_publication(self):
        self._defer_emit=True

    def _sample(self):
        memory=psutil.Process().memory_info().rss/1024/1024
        self._peak=max(self._peak,memory)
        return memory

    def _run(self):
        while not self._stop.wait(.1):
            try:self._sample()
            except Exception:
                self._sampling_error=True
                self._stop.set()

    def close_partial(self):
        self._stop.set()
        if self._sampler is not None and self._sampler.ident is not None and self._sampler is not threading.current_thread():
            self._sampler.join(timeout=1)
            if self._sampler.is_alive():raise RuntimeError("measurement_sampler_unavailable")

    def __enter__(self):
        self.started=perf_counter()
        try:
            self.initial_memory_mb=self._sample()
            self._sampler=threading.Thread(target=self._run,daemon=True,name="inference-rss")
            self._sampler.start()
            return self
        except BaseException:
            try:self.close_partial()
            except Exception:pass
            raise

    def fail(self,code="processing_failed"):
        self.status="failed"
        self.error_code=code if re.fullmatch(r"[a-z0-9_]{1,64}",code) else "processing_failed"

    def __exit__(self,kind,value,traceback):
        try:
            self.close_partial()
            if self._sampling_error:raise RuntimeError("measurement_sampler_unavailable")
            self.final_memory_mb=self._sample()
            self._ready=True
        finally:self._stop.set()
        if kind is not None and self.status=="completed":self.fail()
        if not self._defer_emit:self.publish()
        return False

    def publish(self):
        """Deferred preview emission observes its final, atomic publication outcome."""
        if self._published:return
        self._published=True
        context={"request_id":self.request_id,"job_id":self.job_id,"source_type":self.source_type,"branch":self.branch,
                 "status":self.status,"error_code":self.error_code,**({"profile_id":self.profile_id} if self.profile_id else {})}
        if not self._ready:
            self.logger.error("inference_measurement_failed",extra={**context,"error_code":"measurement_unavailable"})
            return
        self.logger.info("inference_measurement",extra={**context,
            "duration_ms":round((perf_counter()-self.started)*1000,3),
            "initial_memory_mb":round(self.initial_memory_mb,2),
            "memory_mb":round(self.final_memory_mb,2),"peak_memory_mb":round(self._peak,2)})
