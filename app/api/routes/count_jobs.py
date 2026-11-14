from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse

from app.api.dependencies import Principal, require_api_key
from app.domain.models import CountJob
from app.domain.schemas import (
    CountEventPage,
    CountEventResponse,
    CountJobAccepted,
    CountJobCreateRequest,
    CountJobResponse,
    CountLineResponse,
    CountSummaryResponse,
    ErrorResponse,
    NormalizedPoint,
)
from app.services.line_counting import validate_line
from app.domain.models import CountPoint


router = APIRouter(prefix="/v1", tags=["count-jobs"])


def _line_response(job: CountJob) -> CountLineResponse:
    return CountLineResponse(
        point_a=NormalizedPoint(x=job.line.point_a.x, y=job.line.point_a.y),
        point_b=NormalizedPoint(x=job.line.point_b.x, y=job.line.point_b.y),
    )


def public_job(request: Request, job: CountJob) -> CountJobResponse:
    service = request.app.state.count_job_service
    principal = Principal(job.owner_key_id)
    events, _ = service.events(job.count_job_id, principal, 1, 100)
    summary = service.summary(job.count_job_id, principal)
    return CountJobResponse(
        count_job_id=job.count_job_id, source_video_job_id=job.source_video_job_id, status=job.status.value,
        line=_line_response(job), progress_percent=round(job.processed_frames * 100 / max(job.total_frames, 1)),
        processed_frames=job.processed_frames, total_frames=job.total_frames,
        events=[CountEventResponse(**event.__dict__) for event in events],
        summary=[CountSummaryResponse(**item.__dict__) for item in summary],
        created_at=job.created_at, updated_at=job.updated_at, expires_at=job.expires_at,
        error=ErrorResponse(code=job.error_code, message="The count job could not be completed.", request_id="count-job")
        if job.error_code else None,
    )


@router.post("/video-jobs/{videoJobId}/count-jobs", status_code=202, response_model=CountJobAccepted)
def create_count_job(
    videoJobId: str,
    body: CountJobCreateRequest,
    request: Request,
    principal: Principal = Depends(require_api_key),
) -> CountJobAccepted:
    line = validate_line(CountPoint(body.point_a.x, body.point_a.y), CountPoint(body.point_b.x, body.point_b.y))
    job = request.app.state.count_job_service.create(principal, videoJobId, line)
    return CountJobAccepted(
        count_job_id=job.count_job_id, status="queued", created_at=job.created_at, expires_at=job.expires_at,
        line=_line_response(job),
    )


@router.get("/count-jobs/{countJobId}", response_model=CountJobResponse)
def get_count_job(countJobId: str, request: Request, principal: Principal = Depends(require_api_key)) -> CountJobResponse:
    return public_job(request, request.app.state.count_job_service.get(countJobId, principal))


@router.get("/count-jobs/{countJobId}/events", response_model=CountEventPage)
def list_count_events(
    countJobId: str,
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    principal: Principal = Depends(require_api_key),
) -> CountEventPage:
    rows, total = request.app.state.count_job_service.events(countJobId, principal, page, page_size)
    return CountEventPage(items=[CountEventResponse(**row.__dict__) for row in rows], page=page, page_size=page_size, total=total)


@router.get("/count-jobs/{countJobId}/annotated-video", response_class=FileResponse)
def count_annotated_video(countJobId: str, request: Request, principal: Principal = Depends(require_api_key)) -> FileResponse:
    job = request.app.state.count_job_service.artifact(countJobId, principal)
    return FileResponse(job.output_path, media_type="video/mp4", filename="counted.mp4")
