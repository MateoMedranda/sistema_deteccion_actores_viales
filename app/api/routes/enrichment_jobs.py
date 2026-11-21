from __future__ import annotations
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, Path, Query, Request
from app.api.dependencies import Principal, require_api_key
from app.domain.schemas import EnrichedVehiclePage, EnrichmentJobAccepted, EnrichmentJobCreateRequest, EnrichmentJobResponse

router = APIRouter(prefix="/v1/enrichment-jobs", tags=["enrichment-jobs"])

@router.post("", response_model=EnrichmentJobAccepted, status_code=202)
def create_job(payload: EnrichmentJobCreateRequest, request: Request, principal: Principal = Depends(require_api_key)):
    job = request.app.state.enrichment_job_service.create(payload.source.kind, payload.source.source_id, principal.key_id)
    return EnrichmentJobAccepted(enrichment_job_id=job.enrichment_job_id, status="queued", created_at=job.created_at, expires_at=job.expires_at)

@router.get("/{enrichmentJobId}", response_model=EnrichmentJobResponse)
def get_job(enrichment_job_id: Annotated[str, Path(alias="enrichmentJobId")], request: Request, principal: Principal = Depends(require_api_key)):
    return request.app.state.enrichment_job_service.status(enrichment_job_id, principal.key_id)

@router.delete("/{enrichmentJobId}", response_model=EnrichmentJobResponse, status_code=202)
def cancel_job(enrichment_job_id: Annotated[str, Path(alias="enrichmentJobId")], request: Request, principal: Principal = Depends(require_api_key)):
    request.app.state.enrichment_jobs.cancel(enrichment_job_id, principal.key_id)
    return request.app.state.enrichment_job_service.status(enrichment_job_id, principal.key_id)

@router.get("/{enrichmentJobId}/results", response_model=EnrichedVehiclePage)
def get_results(enrichment_job_id: Annotated[str, Path(alias="enrichmentJobId")], request: Request, principal: Principal = Depends(require_api_key), page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100)):
    items, total = request.app.state.enrichment_jobs.results(enrichment_job_id, principal.key_id, page, page_size)
    return EnrichedVehiclePage(items=items, page=page, page_size=page_size, total=total)

from fastapi.responses import Response
from app.api.error_handlers import ApiError
from app.domain.schemas import ErrorResponse, PlatePreviewMetadata
_PREVIEW_SUCCESS={
    "content":{"image/png":{"schema":{"type":"string","format":"binary"}}},
    "headers":{"Cache-Control":{"required":True,"schema":{"type":"string","const":"no-store"}},"X-Plate-Preview-Metadata":{"required":True,"description":"ASCII compact JSON, max 2048 bytes; validate encoded bytes as well as this schema","content":{"application/json":{"schema":{"$ref":"#/components/schemas/PlatePreviewMetadata"}}}}}
}
@router.get("/{enrichmentJobId}/detections/{detectionId}/plate-preview",response_class=Response,
    responses={200:_PREVIEW_SUCCESS,**{code:{"model":ErrorResponse} for code in (401,404,409,410,422,429,503,504)}})
async def get_plate_preview(
    enrichment_job_id:Annotated[str,Path(alias="enrichmentJobId",min_length=1,max_length=128)],
    detection_id:Annotated[int,Path(alias="detectionId",ge=1)],
    request:Request,principal:Principal=Depends(require_api_key),
    profile:Literal["display-contrast-v1"]=Query("display-contrast-v1"),
):
    if set(request.query_params)-{"profile"} or request.headers.get("content-length") not in (None,"0") or request.headers.get("transfer-encoding"):
        raise ApiError(422,"invalid_request","The preview request is invalid.")
    async for chunk in request.stream():
        if chunk:raise ApiError(422,"invalid_request","The preview request is invalid.")
    try:
        value=await request.app.state.plate_preview_service.get(enrichment_job_id,detection_id,principal.key_id,request.state.request_id,request.is_disconnected)
    except ApiError as exc:
        if exc.status_code==429:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=429,content={"code":exc.code,"message":exc.message,"request_id":request.state.request_id},headers={"Retry-After":"1","Cache-Control":"no-store"})
        raise
    return Response(value.png,media_type="image/png",headers={"Cache-Control":"no-store","X-Plate-Preview-Metadata":value.metadata})
