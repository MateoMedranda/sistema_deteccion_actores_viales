from uuid import UUID
from fastapi import APIRouter,Depends,Query,Request,Response
from app.api.dependencies import Principal,require_api_key
from app.services.video_detail_access import closed_query as query
from app.domain.directed_count import DirectedCountRequest,DirectedCount
router=APIRouter(prefix='/v1/video-jobs',tags=['directed-count'])
@router.put('/{job_id}/playback/directed-count',response_model=DirectedCount)
def configure(job_id:str,body:DirectedCountRequest,request:Request,principal:Principal=Depends(require_api_key)):
 query(request,[]);return request.app.state.directed_count.configure(job_id,principal.key_id,body.model_dump(mode='json'))
@router.get('/{job_id}/playback/directed-count',response_model=DirectedCount)
def get(job_id:str,request:Request,generation:UUID,at_us:int=Query(default=0,ge=0,le=2**53-1),revision:int|None=Query(default=None,ge=0,le=2**53-1),principal:Principal=Depends(require_api_key)):
 query(request,['generation','at_us','revision']);return request.app.state.directed_count.snapshot(job_id,principal.key_id,str(generation),at_us,revision)
@router.delete('/{job_id}/playback/directed-count',status_code=204)
def disable(job_id:str,request:Request,generation:UUID,expected_revision:int=Query(ge=0,le=2**53-1),principal:Principal=Depends(require_api_key)):
 query(request,['generation','expected_revision']);request.app.state.directed_count.disable(job_id,principal.key_id,str(generation),expected_revision);return Response(status_code=204)
