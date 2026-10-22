from __future__ import annotations

from typing import Annotated
from time import perf_counter

from fastapi import APIRouter, Depends, File, Path, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

from app.api.dependencies import require_api_key
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
    _: None = Depends(require_api_key),
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
    _: None = Depends(require_api_key),
) -> FileResponse:
    artifact, expired = request.app.state.service.artifacts.get(request_id)
    if artifact is None:
        if expired:
            raise ApiError(410, "artifact_expired", "The annotated image has expired.")
        raise ApiError(404, "artifact_not_found", "No annotated image was found for this request.")
    return FileResponse(artifact.path, media_type="image/jpeg", filename="annotated-image.jpg")
