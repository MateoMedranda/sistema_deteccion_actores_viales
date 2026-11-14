from __future__ import annotations

from app.api.dependencies import Principal
from app.api.error_handlers import ApiError
from app.core.config import Settings
from app.domain.models import CountJob, CountJobStatus, CountLine, VideoJobStatus
from app.services.count_job_store import CountJobStore
from app.services.video_artifacts import VideoArtifactStore
from app.services.video_job_store import VideoJobStore


class CountJobService:
    def __init__(
        self, settings: Settings, store: CountJobStore, video_store: VideoJobStore, artifacts: VideoArtifactStore, logger
    ) -> None:
        self.settings, self.store, self.video_store, self.artifacts, self.logger = settings, store, video_store, artifacts, logger

    def create(self, principal: Principal, source_video_job_id: str, line: CountLine) -> CountJob:
        source = self.video_store.get(source_video_job_id, principal.key_id)
        if source.status is not VideoJobStatus.COMPLETED:
            raise ApiError(409, "source_not_ready", "The source video is not available for counting.")
        job = self.store.create(source.job_id, principal.key_id, line, source.metadata.total_frames, source.expires_at)
        self.logger.info("count_job_created", extra={
            "count_job_id": job.count_job_id, "source_video_job_id": source.job_id, "owner_key_id": principal.key_id,
        })
        return job

    def get(self, count_job_id: str, principal: Principal) -> CountJob:
        return self.store.get(count_job_id, principal.key_id)

    def events(self, count_job_id: str, principal: Principal, page: int, page_size: int):
        return self.store.events(count_job_id, principal.key_id, page, page_size)

    def summary(self, count_job_id: str, principal: Principal):
        return self.store.summary(count_job_id, principal.key_id)

    def artifact(self, count_job_id: str, principal: Principal):
        job = self.get(count_job_id, principal)
        if job.status is not CountJobStatus.COMPLETED or job.output_path is None or not job.output_path.is_file():
            raise ApiError(404, "count_artifact_not_found", "The requested resource is unavailable.")
        return job

    def cleanup(self) -> None:
        for path in self.store.cleanup():
            self.artifacts.remove(path)
