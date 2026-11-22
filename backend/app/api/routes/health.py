from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.domain.schemas import HealthResponse, EnrichmentReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health/live", response_model=HealthResponse)
def liveness() -> HealthResponse:
    return HealthResponse(status="alive")


@router.get("/health/ready", response_model=HealthResponse)
def readiness(request: Request):
    if not request.app.state.ready:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return HealthResponse(status="ready")


@router.get("/health/video-ready", response_model=HealthResponse)
def video_readiness(request: Request):
    if not request.app.state.ready or not request.app.state.video_tools_ready:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return HealthResponse(status="ready")


@router.get("/health/enrichment-ready", response_model=EnrichmentReadinessResponse,
            responses={503: {"model": EnrichmentReadinessResponse}})
def enrichment_readiness(request: Request):
    processor = request.app.state.enrichment_job_service.processor
    capabilities = processor.capabilities
    ready = request.app.state.ready and all(v == "ready" for v in capabilities.values())
    body = EnrichmentReadinessResponse(status="ready" if ready else "not_ready", capabilities=capabilities)
    if not ready:
        return JSONResponse(status_code=503, content=body.model_dump())
    return body


from app.domain.schemas import ImageUploadPolicy

@router.get("/health/image-policy", response_model=ImageUploadPolicy)
def image_upload_policy(request: Request):
    settings=request.app.state.settings
    return ImageUploadPolicy(media_types=["image/jpeg","image/png"],max_upload_bytes=settings.max_upload_bytes,max_image_pixels=settings.max_image_pixels)
