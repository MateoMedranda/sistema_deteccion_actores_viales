"""Safe process-RSS observations; memory is not exclusive allocation per job."""
import logging
import re
import threading
from time import perf_counter
import psutil

class InferenceMetrics:
    def __init__(self, logger: logging.Logger, branch: str, *, request_id=None, job_id=None, source_type="image", profile_id=None):
        self.logger, self.branch = logger, branch
        self.request_id, self.job_id, self.source_type = request_id, job_id, source_type
        self.profile_id=profile_id if profile_id=="display-contrast-v1" else None
        self.status, self.error_code = "completed", None
        self._stop = threading.Event()
        self._peak = 0.0
        self._sampler = None

    def _sample(self):
        memory = psutil.Process().memory_info().rss / 1024 / 1024
        self._peak = max(self._peak, memory)
        return memory

    def _run(self):
        while not self._stop.wait(.1):
            self._sample()

    def __enter__(self):
        self.started = perf_counter()
        self.initial_memory_mb = self._sample()
        self._sampler = threading.Thread(target=self._run, daemon=True, name="inference-rss")
        self._sampler.start()
        return self

    def fail(self, code="processing_failed"):
        self.status = "failed"
        self.error_code = code if re.fullmatch(r"[a-z0-9_]{1,64}", code) else "processing_failed"

    def __exit__(self, kind, value, traceback):
        self._stop.set()
        if self._sampler:
            self._sampler.join(timeout=1)
        final = self._sample()
        if kind is not None and self.status == "completed":
            self.fail()
        self.logger.info("inference_measurement", extra={
            "request_id": self.request_id, "job_id": self.job_id,
            "source_type": self.source_type, "branch": self.branch,
            "duration_ms": round((perf_counter() - self.started) * 1000, 3),
            "initial_memory_mb": round(self.initial_memory_mb, 2),
            "memory_mb": round(final, 2), "peak_memory_mb": round(self._peak, 2),
            "status": self.status, "error_code": self.error_code,
            **({"profile_id":self.profile_id} if self.profile_id else {}),
        })
        return False
