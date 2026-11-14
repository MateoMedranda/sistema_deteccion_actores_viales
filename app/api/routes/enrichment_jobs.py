from __future__ import annotations
from typing import Annotated
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
