from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import FileResponse

from app.api.dependencies import Principal, require_api_key
from app.api.error_handlers import ApiError
from app.domain.models import VideoJob, VideoJobStatus
from app.domain.schemas import (
    BoundingBox,
    DetectionPage,
    FrameDetectionResponse,
    TemporaryVideo,
    VideoClassSummary,
    VideoJobAccepted,
    VideoJobResponse,
)

router = APIRouter(prefix="/v1/video-jobs", tags=["video-jobs"])


def public_job(job: VideoJob) -> VideoJobResponse:
    return VideoJobResponse(
        job_id=job.job_id, status=job.status.value,
        processing_phase=job.processing_phase,frame_total_confirmed=job.frame_total_confirmed,video_metadata=job.video_metadata,eligible_track_count=job.eligible_track_count,classes_present=job.classes_present,
        progress_percent=min(100,round(job.processed_frames * 100 / max(1,job.metadata.total_frames))),
        processed_frames=job.processed_frames, total_frames=job.metadata.total_frames,
        created_at=job.created_at, updated_at=job.updated_at, expires_at=job.expires_at,
        error={"code": job.error_code, "message": "The video job could not be completed.", "request_id": "job"}
        if job.error_code else None,
    )


@router.post("", status_code=202, response_model=VideoJobAccepted)
async def create_video_job(request: Request, video: UploadFile = File(...), principal: Principal = Depends(require_api_key)) -> VideoJobAccepted:
    job = await request.app.state.video_job_service.create(principal, video)
    return VideoJobAccepted(job_id=job.job_id, status="queued", created_at=job.created_at)


@router.get("/{job_id}", response_model=VideoJobResponse)
def get_video_job(job_id: str, request: Request, principal: Principal = Depends(require_api_key)) -> VideoJobResponse:
    return public_job(request.app.state.video_jobs.get(job_id, principal.key_id))


@router.delete("/{job_id}", status_code=202, response_model=VideoJobResponse)
def cancel_video_job(job_id: str, request: Request, principal: Principal = Depends(require_api_key)) -> VideoJobResponse:
    job = request.app.state.video_job_service.cancel(job_id, principal)
    return public_job(job)


@router.get("/{job_id}/detections", response_model=DetectionPage)
def list_detections(
    job_id: str,
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    principal: Principal = Depends(require_api_key),
) -> DetectionPage:
    rows, total = request.app.state.video_jobs.detections(job_id, principal.key_id, page, page_size)
    return DetectionPage(
        items=[FrameDetectionResponse(
            frame_index=row.frame_index, track_id=row.track_id, class_id=row.class_id,
            class_name=row.class_name, confidence=row.confidence,
            bbox=BoundingBox(x_min=row.x_min, y_min=row.y_min, x_max=row.x_max, y_max=row.y_max),
        ) for row in rows],
        page=page, page_size=page_size, total=total,
    )


@router.get("/{job_id}/annotated-video", response_model=TemporaryVideo)
def annotated_video_metadata(job_id: str, request: Request, principal: Principal = Depends(require_api_key)) -> TemporaryVideo:
    job = request.app.state.video_jobs.get(job_id, principal.key_id)
    if job.status is not VideoJobStatus.COMPLETED or job.output_path is None or not job.output_path.is_file():
        raise ApiError(409, "result_not_ready", "The annotated video is not available yet.")
    return TemporaryVideo(url=f"/api/v1/video-jobs/{job_id}/annotated-video/content", expires_at=job.expires_at)


@router.get("/{job_id}/annotated-video/content", response_class=FileResponse)
def annotated_video_content(job_id: str, request: Request, principal: Principal = Depends(require_api_key)) -> FileResponse:
    job = request.app.state.video_jobs.get(job_id, principal.key_id)
    if job.status is not VideoJobStatus.COMPLETED or job.output_path is None or not job.output_path.is_file():
        raise ApiError(404, "artifact_not_found", "The requested resource is unavailable.")
    return FileResponse(job.output_path, media_type="video/mp4", filename="annotated.mp4")


@router.get("/{job_id}/summary", response_model=list[VideoClassSummary])
def detection_summary(job_id: str, request: Request, principal: Principal = Depends(require_api_key)) -> list[VideoClassSummary]:
    counts = request.app.state.video_jobs.summary(job_id, principal.key_id)
    return [VideoClassSummary(class_name=name, detections=count) for name, count in counts.items()]
