from __future__ import annotations

from app.api.error_handlers import ApiError
from app.services.job_intents import key_hash,source_fingerprint
from app.core.config import Settings
from app.domain.models import Detection, FrameDetection
from app.services.enrichment_job_store import EnrichmentJobStore
from app.services.image_detection_store import ImageDetectionStore
from app.services.track_consolidation import select_track_evidence


class EnrichmentJobService:
    def __init__(self, settings: Settings, jobs: EnrichmentJobStore, images: ImageDetectionStore, video_jobs) -> None:
        self.settings, self.jobs, self.images, self.video_jobs = settings, jobs, images, video_jobs
        self.processor = None

    def create(self, kind: str, source_id: str, owner_key_id: str, idempotency_key: str | None = None):
        source = self.resolve(kind, source_id, owner_key_id)
        units = self.units_for_source(kind, source, owner_key_id)
        hashed=key_hash(idempotency_key);fingerprint=source_fingerprint(kind,source_id) if hashed else None
        replay=self.jobs.find_intent(owner_key_id,hashed,fingerprint)
        if replay:return replay
        evidence=getattr(self,"progressive",None)
        if kind=="video" and evidence and evidence.store.exists(source_id):
            with evidence.store.lock:
                evidence.store.row(source_id,owner_key_id)
                pending=evidence.store.db.execute("SELECT payload FROM p_tracks WHERE job=?",(source_id,)).fetchall()
                if any(not __import__("json").loads(x[0])["final"] for x in pending):
                    raise ApiError(409,"enrichment_not_ready","The progressive enrichment is still running.")
        if self.processor is None or not self.processor.usable:
            raise ApiError(503, "enrichment_unavailable", "Enrichment is not available at this time.")
        if not units: raise ApiError(400, "no_eligible_vehicles", "The source has no eligible vehicle detections.")
        return self.jobs.create(kind,source_id,owner_key_id,len(units),source.expires_at,idempotency_key_hash=hashed,request_fingerprint=fingerprint)

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

    def cached_results(self,job):
        evidence=getattr(self,"progressive",None)
        if job.source_kind!="video" or not evidence or not evidence.store.exists(job.source_id):return None
        import json
        from app.services.plate_consensus import PlateCandidate,consensus
        results=[]
        with evidence.store.lock:
            evidence.store.row(job.source_id,job.owner_key_id)
            units=self.units_for_source("video",self.resolve("video",job.source_id,job.owner_key_id),job.owner_key_id)
            for unit in units:
                rows=evidence.store.db.execute("SELECT * FROM p_evidence WHERE job=? AND track=? AND candidate=1 ORDER BY confidence DESC,idx",(job.source_id,unit["track_id"])).fetchall()
                outputs=[(r["idx"],json.loads(r["result"])) for r in rows if r["result"]]
                valid=[(i,r) for i,r in outputs if "attributes" in r]
                attributes=valid[0][1]["attributes"] if valid else dict(status="failed",items=[],error_code="crop_unavailable")
                plate=valid[0][1]["plate"] if valid else dict(status="failed",used_enhancement=False,evidence_frame_indexes=[],error_code="crop_unavailable")
                candidates=[PlateCandidate(r["plate"].get("text") or "",r["plate"].get("ocr_confidence") or 0,r["plate"].get("localizer_confidence") or 0,1.0,i) for i,r in valid if r["plate"].get("status")=="read"]
                winner=consensus(candidates,self.processor.accept_threshold)
                if winner:
                    observed=next(r["plate"] for i,r in valid if i==winner.frame_index)
                    plate={**observed,"status":"read","text":winner.text,"ocr_confidence":winner.ocr_confidence,"evidence_frame_indexes":[c.frame_index for c in candidates if c.text==winner.text]}
                elif candidates:plate={**plate,"status":"unreadable","text":None}
                results.append(dict(vehicle_key=f"track-{unit['track_id']}",detection_id=unit["detection_id"],track_id=unit["track_id"],class_id=unit["class_id"],class_name=unit["class_name"],evidence_frame_indexes=[r["idx"] for r in rows],attributes_status=attributes["status"],plate_status=plate["status"],attributes=attributes["items"],plate=plate,error_code=attributes.get("error_code") or plate.get("error_code")))
        return results

    def status(self, job_id: str, owner_key_id: str) -> dict:
        job = self.jobs.get(job_id, owner_key_id); results, total = self.jobs.results(job_id, owner_key_id, 1, 100) if job.status.value in {"completed", "processing"} else ([], 0)
        return {"enrichment_job_id": job.enrichment_job_id, "source": {"kind": job.source_kind, "source_id": job.source_id}, "status": job.status.value, "processed_units": job.processed_units, "total_units": job.total_units, "progress_percent": 100 if job.status.value == "completed" else int(100 * job.processed_units / max(1, job.total_units)), "results_ready": total, "created_at": job.created_at, "updated_at": job.updated_at, "expires_at": job.expires_at, "error": None if not job.error_code else {"code": job.error_code, "message": "The enrichment job could not be completed.", "request_id": "job"}}
