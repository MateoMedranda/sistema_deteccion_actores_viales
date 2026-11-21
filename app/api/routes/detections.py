from __future__ import annotations

from typing import Annotated
from time import perf_counter

from fastapi import APIRouter, Depends, File, Path, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from app.api.dependencies import Principal, require_api_key
from app.api.error_handlers import ApiError
from app.domain.schemas import DetectionResponse, ErrorResponse
from app.services.image_validation import ImageValidator

router = APIRouter(prefix="/v1/detections", tags=["detections"])


@router.post(
    "/images",
    response_model=DetectionResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        415: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def analyze_image(
    request: Request,
    image: UploadFile = File(...),
    principal: Principal = Depends(require_api_key),
) -> DetectionResponse:
    started = perf_counter()
    validator = ImageValidator(request.app.state.settings)
    request.app.state.service.begin(request.state.request_id)
    try:
        try:
            validated = await validator.validate(image)
        except ApiError as error:
            request.app.state.service.reject(
                request.state.request_id,
                error.code,
                round((perf_counter() - started) * 1000),
            )
            raise
        validation_ms = round((perf_counter() - started) * 1000)
        return await run_in_threadpool(
            request.app.state.service.analyze,
            request.state.request_id,
            validated,
            validation_ms,
            principal.key_id,
        )
    finally:
        await image.close()


@router.get(
    "/{requestId}/annotated-image",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 410: {"model": ErrorResponse}},
)
def get_annotated_image(
    request_id: Annotated[str, Path(alias="requestId")],
    request: Request,
    principal: Principal = Depends(require_api_key),
) -> Response:
    data = request.app.state.service.artifacts.read(request_id, principal.key_id)
    return Response(data, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


@router.get(
    "/{requestId}/original-image",
    responses={200: {"content": {"image/png": {"schema": {"type": "string", "format": "binary"}}}},
               401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 410: {"model": ErrorResponse}},
    response_class=Response,
)
def get_original_image(
    request_id: Annotated[str, Path(alias="requestId")],
    request: Request,
    principal: Principal = Depends(require_api_key),
) -> Response:
    data, source = request.app.state.image_sources.read_original(request_id, principal.key_id)
    return Response(data, media_type=source.media_type, headers={"Cache-Control": "no-store"})
