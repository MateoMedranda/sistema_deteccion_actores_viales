from __future__ import annotations

import threading

from app.services.video_processing import VideoProcessingError, VideoProcessor


class VideoWorker:
    def __init__(self, processor: VideoProcessor, store, logger) -> None:
        self.processor, self.store, self.logger = processor, store, logger
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="video-worker", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=3)

    def _run(self) -> None:
        while not self._stop.wait(0.25):
            job = self.store.dequeue()
            if job is None:
                continue
            try:
                self.processor.process(job)
            except VideoProcessingError as exc:
                self.store.fail(job.job_id, str(exc))
                self.processor.artifacts.remove(job.staged_path)
                self.logger.info("video_job_failed", extra={"job_id": job.job_id, "error_code": str(exc)})
            except Exception as exc:
                self.store.fail(job.job_id, "processing_failed")
                self.processor.artifacts.remove(job.staged_path)
                self.logger.exception("video_job_failed", extra={
                    "job_id": job.job_id,
                    "error_code": "processing_failed",
                    "exception_type": type(exc).__name__,
                })
