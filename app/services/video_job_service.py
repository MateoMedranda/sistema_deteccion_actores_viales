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

    async def create(self, principal: Principal, upload: UploadFile, idempotency_key: str | None = None) -> VideoJob:
        staged = self.artifacts.staged_input_path()
        try:
            hasher=hashlib.sha256(((upload.content_type or "").strip().lower()+"\0").encode()) if idempotency_key is not None else None
            metadata=await VideoValidator(self.settings,self.probe).stage_and_validate(upload,staged,hasher)
            job=self.store.create(principal.key_id,metadata,staged,idempotency_key_hash=key_hash(idempotency_key),request_fingerprint=hasher.hexdigest() if hasher else None)
            if job.staged_path!=staged:self.artifacts.remove(staged)
            return job
        except Exception:
            self.artifacts.remove(staged)
            raise
        finally:
            await upload.close()

    def cancel(self, job_id: str, principal: Principal) -> VideoJob:
        job = self.store.cancel(job_id, principal.key_id)
        for path in (job.staged_path,job.output_path):
            if path and not self.store.in_use(path):self.artifacts.remove(path)
        return job

    def cleanup(self) -> None:
        for path in self.store.cleanup():
            if not self.store.in_use(path):
                try:self.artifacts.remove(path);self.store._purged.discard(path)
                except PermissionError:pass
