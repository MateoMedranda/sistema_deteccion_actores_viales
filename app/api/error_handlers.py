from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message, "request_id": request_id},
    )


async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a stable public shape without exposing request internals."""
    return await api_error_handler(
        request,
        ApiError(422, "invalid_request", "The request does not satisfy the required format."),
    )


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    message = "The requested resource is unavailable." if exc.status_code == 404 else "The request could not be processed."
    return await api_error_handler(request, ApiError(exc.status_code, "http_error", message))
