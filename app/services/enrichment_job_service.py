from __future__ import annotations

from app.api.error_handlers import ApiError
from app.core.config import Settings
from app.domain.models import Detection, FrameDetection
from app.services.enrichment_job_store import EnrichmentJobStore
from app.services.image_detection_store import ImageDetectionStore
from app.services.track_consolidation import select_track_evidence


class EnrichmentJobService:
    def __init__(self, settings: Settings, jobs: EnrichmentJobStore, images: ImageDetectionStore, video_jobs) -> None:
        self.settings, self.jobs, self.images, self.video_jobs = settings, jobs, images, video_jobs
        self.processor = None

    def create(self, kind: str, source_id: str, owner_key_id: str):
        source = self.resolve(kind, source_id, owner_key_id)
        units = self.units_for_source(kind, source, owner_key_id)
        if self.processor is None or not self.processor.usable:
            raise ApiError(503, "enrichment_unavailable", "Enrichment is not available at this time.")
        if not units: raise ApiError(400, "no_eligible_vehicles", "The source has no eligible vehicle detections.")
        return self.jobs.create(kind, source_id, owner_key_id, len(units), source.expires_at)

    def resolve(self, kind: str, source_id: str, owner_key_id: str):
        if kind == "image": return self.images.get(source_id, owner_key_id)
        if kind == "video":
            job = self.video_jobs.get(source_id, owner_key_id)
            if job.status.value != "completed": raise ApiError(409, "source_not_ready", "The source is not ready for enrichment.")
            if job.staged_path is None or not job.staged_path.is_file(): raise ApiError(409, "source_not_available", "The source is not available for enrichment.")
            return job
        raise ApiError(400, "invalid_source", "The source reference is invalid.")

    def units_for_source(self, kind: str, source, owner_key_id: str) -> list[dict]:
        vehicle_classes = self.settings.vehicle_class_set()
        if kind == "image":
            return [{"detection_id": index + 1, "track_id": None, "class_id": d.class_id, "class_name": d.class_name, "frame_index": None, "bbox": d} for index, d in enumerate(source.detections) if d.class_name.lower() in vehicle_classes]
        return select_track_evidence(self.video_jobs.all_detections(source.job_id, owner_key_id), vehicle_classes, self.settings.max_evidence_frames_per_track)

    def status(self, job_id: str, owner_key_id: str) -> dict:
        job = self.jobs.get(job_id, owner_key_id); results, total = self.jobs.results(job_id, owner_key_id, 1, 100) if job.status.value in {"completed", "processing"} else ([], 0)
        return {"enrichment_job_id": job.enrichment_job_id, "source": {"kind": job.source_kind, "source_id": job.source_id}, "status": job.status.value, "processed_units": job.processed_units, "total_units": job.total_units, "progress_percent": 100 if job.status.value == "completed" else int(100 * job.processed_units / max(1, job.total_units)), "results_ready": total, "created_at": job.created_at, "updated_at": job.updated_at, "expires_at": job.expires_at, "error": None if not job.error_code else {"code": job.error_code, "message": "The enrichment job could not be completed.", "request_id": "job"}}
