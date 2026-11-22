from fastapi import APIRouter,Depends,Request
from app.api.dependencies import require_api_key,Principal
from app.domain.schemas import WebPolicy
from app.services.web_policy_service import WebPolicyService
router=APIRouter(tags=["web-policy"])
@router.get("/v1/web-policy",response_model=WebPolicy)
def policy(request:Request,principal:Principal=Depends(require_api_key)):
    return WebPolicyService(request.app.state.settings,request.app.state).get()
