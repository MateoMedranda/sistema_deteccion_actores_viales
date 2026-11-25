from fastapi import APIRouter, Depends, Request
from app.api.dependencies import Principal, require_api_key
from app.api.routes.video_playback import query
from app.services.video_detail_capabilities import capabilities
from app.domain.video_detail_contracts import Capabilities
router=APIRouter(prefix='/v1/video-jobs',tags=['video-detail'])
@router.get('/{job_id}/playback/capabilities',response_model=Capabilities)
def get_capabilities(job_id:str,request:Request,principal:Principal=Depends(require_api_key)):
 query(request,[])
 return capabilities(request.app.state.progressive_store,job_id,principal.key_id)

from uuid import UUID
from app.domain.detection_summary import DetectionSummary
@router.get('/{job_id}/playback/detection-summary',response_model=DetectionSummary)
def summary(job_id:str,request:Request,generation:UUID,principal:Principal=Depends(require_api_key)):
 query(request,['generation'])
 return request.app.state.detection_inventory.snapshot(job_id,principal.key_id,str(generation))
