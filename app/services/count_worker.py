from __future__ import annotations

import threading

from app.services.count_processing import CountProcessingError, CountProcessor


class CountWorker:
    def __init__(self, processor: CountProcessor, store, artifacts, logger) -> None:
        self.processor, self.store, self.artifacts, self.logger = processor, store, artifacts, logger
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="count-worker", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=3)

    def _run(self) -> None:
        while not self._stop.wait(0.1):
            job = self.store.dequeue()
            if job is None:
                continue
            try:
                self.processor.process(job)
            except CountProcessingError as exc:
                if str(exc) not in {"count_cancelled", "count_expired", "count_not_active"}:
                    self.store.fail(job.count_job_id, str(exc))
                self.logger.info("count_job_failed", extra={
                    "count_job_id": job.count_job_id, "source_video_job_id": job.source_video_job_id,
                    "error_code": str(exc),
                })
            except Exception as exc:
                self.store.fail(job.count_job_id, "count_processing_failed")
                self.logger.exception("count_job_failed", extra={
                    "count_job_id": job.count_job_id, "source_video_job_id": job.source_video_job_id,
                    "error_code": "count_processing_failed", "exception_type": type(exc).__name__,
                })
