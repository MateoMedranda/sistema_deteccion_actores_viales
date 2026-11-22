from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from app.api.dependencies import authenticate_api_key
from app.api.error_handlers import ApiError
from app.core.config import Settings


async def reject_unauthorized_video_upload(
    request: Request, call_next, settings: Settings
) -> Response:
    """Authenticate video submissions before Starlette parses multipart data or stages a file."""
    if request.method == "POST" and request.url.path == "/api/v1/video-jobs":
        try:
            authenticate_api_key(settings, request.headers.get("X-API-Key"))
        except ApiError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "code": exc.code,
                    "message": exc.message,
                    "request_id": getattr(request.state, "request_id", "unknown"),
                },
            )
    return await call_next(request)
