import json
from typing import Literal
from uuid import UUID
from fastapi import APIRouter,Depends,Request,Response
from app.api.dependencies import Principal,require_api_key
from app.api.error_handlers import ApiError
from app.api.routes.video_playback import query
from app.domain.video_detail import InspectionRequest
from app.domain.video_inspection import Inspection
from app.services.progressive_media import media
from app.services.video_inspection_preview import preview
router=APIRouter(prefix='/v1/video-jobs',tags=['video-inspections'])
@router.post('/{job_id}/playback/inspections',status_code=202,response_model=Inspection)
def create(job_id:str,body:InspectionRequest,request:Request,principal:Principal=Depends(require_api_key)):
 query(request,[])
 return request.app.state.video_inspections.admit(job_id,principal.key_id,body.model_dump(mode='json'))
@router.get('/{job_id}/playback/inspections/{inspection_id}',response_model=Inspection)
def get(job_id:str,inspection_id:UUID,request:Request,principal:Principal=Depends(require_api_key)):
 query(request,[])
 return request.app.state.video_inspections.get(job_id,principal.key_id,str(inspection_id))
@router.get('/{job_id}/playback/inspections/{inspection_id}/assets/{asset_id}/{kind}')
def asset(job_id:str,inspection_id:UUID,asset_id:UUID,kind:Literal['vehicle','plate'],request:Request,principal:Principal=Depends(require_api_key)):
 query(request,[]);service=request.app.state.video_inspections
 path=service.resource(job_id,principal.key_id,str(inspection_id),str(asset_id),kind)
 response=media(service.store,job_id,principal.key_id,path,request,'image/png',service.settings.video_inspection_max_resource_bytes)
 response.headers['ETag']='"'+str(asset_id)+'"';return response
@router.get('/{job_id}/playback/inspections/{inspection_id}/plate-preview')
def plate_preview(job_id:str,inspection_id:UUID,request:Request,profile:str='display-contrast-v1',principal:Principal=Depends(require_api_key)):
 query(request,['profile']);png,metadata=preview(request.app.state.video_inspections,job_id,principal.key_id,str(inspection_id),profile)
 return Response(png,media_type='image/png',headers={'Cache-Control':'no-store','Cross-Origin-Resource-Policy':'same-origin','X-Plate-Preview-Metadata':json.dumps(metadata,separators=(',',':'))})
