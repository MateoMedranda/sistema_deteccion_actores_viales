from uuid import UUID
from fastapi import APIRouter,Depends,Query,Request
from app.api.dependencies import Principal,require_api_key
from app.domain.count_lines import CollectionWrite,LegacyImport,Collection,CountSnapshot
from app.services.video_detail_access import closed_query
router=APIRouter(prefix='/v1/video-jobs',tags=['count-lines'])
@router.get('/{job_id}/playback/count-lines',response_model=Collection)
def get(job_id:str,request:Request,generation:UUID,p:Principal=Depends(require_api_key)):
 closed_query(request,['generation']);return request.app.state.count_lines.descriptor(job_id,p.key_id,str(generation))
@router.put('/{job_id}/playback/count-lines',response_model=Collection)
def put(job_id:str,body:CollectionWrite,request:Request,p:Principal=Depends(require_api_key)):
 closed_query(request,[]);return request.app.state.count_lines.configure(job_id,p.key_id,body.model_dump(mode='json'))
@router.get('/{job_id}/playback/count-lines/counts',response_model=CountSnapshot)
def counts(job_id:str,request:Request,generation:UUID,revision:int=Query(ge=0,le=2**53-1),at_us:int=Query(ge=0,le=2**53-1),p:Principal=Depends(require_api_key)):
 closed_query(request,['generation','revision','at_us']);return request.app.state.count_lines.snapshot(job_id,p.key_id,str(generation),revision,at_us)
@router.post('/{job_id}/playback/count-lines/import-legacy',response_model=Collection)
def legacy(job_id:str,body:LegacyImport,request:Request,p:Principal=Depends(require_api_key)):
 closed_query(request,[]);return request.app.state.count_lines.import_legacy(job_id,p.key_id,body.model_dump(mode='json'))
