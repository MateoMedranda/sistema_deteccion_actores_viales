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
        with self.store._lock,self.store._connection:
            self.store._connection.execute("UPDATE video_jobs SET status='cancelled',processing_phase='cancelled' WHERE status='processing'")
        self._thread.join()

    def _run(self) -> None:
        while not self._stop.wait(0.25):
            job = self.store.dequeue()
            if job is None:
                continue
            try:
                self.processor.process(job)
            except VideoProcessingError as exc:
                if not self.store.is_cancelled(job.job_id):
                    self.store.fail(job.job_id,str(exc))
                    self.logger.info("video_job_failed",extra={"job_id":job.job_id,"error_code":str(exc)})
                self.processor.artifacts.remove(job.staged_path)
            except Exception as exc:
                self.store.fail(job.job_id, "processing_failed")
                self.processor.artifacts.remove(job.staged_path)
                self.logger.error("video_job_failed", extra={
                    "job_id": job.job_id,
                    "error_code": "processing_failed",
                    "exception_type": type(exc).__name__,
                })

            finally:
                self.store.release(job.job_id)
