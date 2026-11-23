from __future__ import annotations

from pathlib import Path
import hashlib
from app.services.job_intents import key_hash

from fastapi import UploadFile

from app.adapters.video_probe import VideoProbe
from app.api.dependencies import Principal
from app.core.config import Settings
from app.domain.models import VideoJob
from app.services.video_artifacts import VideoArtifactStore
from app.services.video_job_store import VideoJobStore
from app.services.video_validation import VideoValidator


class VideoJobService:
    def __init__(self, settings: Settings, probe: VideoProbe, store: VideoJobStore, artifacts: VideoArtifactStore) -> None:
        self.settings, self.probe, self.store, self.artifacts = settings, probe, store, artifacts

    async def create(self, principal: Principal, upload: UploadFile, idempotency_key: str | None = None, progressive: bool = False) -> VideoJob:
        staged = self.artifacts.staged_input_path()
        try:
            hasher=hashlib.sha256(((upload.content_type or "").strip().lower()+"\0").encode()) if idempotency_key is not None else None
            if hasher is not None and progressive:hasher.update(b"progressive\0")
            metadata=await VideoValidator(self.settings,self.probe).stage_and_validate(upload,staged,hasher)
            with self.store._lock:
                job=self.store.create(principal.key_id,metadata,staged,idempotency_key_hash=key_hash(idempotency_key),request_fingerprint=hasher.hexdigest() if hasher else None)
                if progressive:
                    self.progressive.create(job.job_id,principal.key_id,job.staged_path,
                        dict(width=metadata.width,height=metadata.height,fps=metadata.fps,duration=metadata.duration_seconds),job.expires_at)
            if job.staged_path!=staged:self.artifacts.remove(staged)
            return job
        except Exception:
            self.artifacts.remove(staged)
            raise
        finally:
            await upload.close()

    def cancel(self, job_id: str, principal: Principal) -> VideoJob:
        if hasattr(self,"progressive") and self.progressive.exists(job_id):
            job=self.store.get(job_id,principal.key_id)
            self.progressive.withdraw(job_id,principal.key_id)
            from dataclasses import replace
            from app.domain.models import VideoJobStatus
            return replace(job,status=VideoJobStatus.CANCELLED)
        job = self.store.cancel(job_id, principal.key_id)
        for path in (job.staged_path,job.output_path):
            if path and not self.store.in_use(path):self.artifacts.remove(path)
        return job

    def cleanup(self) -> None:
        for path in self.store.cleanup():
            if not self.store.in_use(path) and not getattr(self.artifacts,"retained",lambda p:False)(path):
                try:self.artifacts.remove(path);self.store._purged.discard(path)
                except PermissionError:pass
