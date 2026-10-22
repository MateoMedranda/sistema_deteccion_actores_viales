from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.domain.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health/live", response_model=HealthResponse)
def liveness() -> HealthResponse:
    return HealthResponse(status="alive")


@router.get("/health/ready", response_model=HealthResponse)
def readiness(request: Request):
    if not request.app.state.ready:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return HealthResponse(status="ready")
