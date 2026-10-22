from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.adapters.detector_protocol import Detector
from app.api.error_handlers import (
    ApiError,
    api_error_handler,
    http_error_handler,
    request_validation_error_handler,
)
from app.api.routes import detections, health
from app.core.config import Settings
from app.core.lifespan import build_lifespan


def create_app(settings: Settings | None = None, detector: Detector | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(
        title="Road Actor Detection API",
        version="1.0.0",
        description="Protected single-image road actor detection service.",
        lifespan=build_lifespan(settings, detector),
    )
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.include_router(health.router)
    app.include_router(detections.router, prefix="/api")

    @app.middleware("http")
    async def request_identity(request: Request, call_next) -> Response:
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    return app


app = create_app()
