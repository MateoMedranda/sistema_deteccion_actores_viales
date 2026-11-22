from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from app.api.routes import web_policy
from app.domain.schemas import PlatePreviewMetadata
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from starlette.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.adapters.detector_protocol import Detector
from app.api.error_handlers import (
    ApiError,
    api_error_handler,
    http_error_handler,
    request_validation_error_handler,
)
from app.api.upload_auth import reject_unauthorized_video_upload
from app.api.routes import count_jobs, detections, enrichment_jobs, health, video_jobs
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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origin_list(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key"],
        expose_headers=["X-Plate-Preview-Metadata"],
    )
    app.include_router(health.router)
    app.include_router(web_policy.router, prefix="/api")
    app.include_router(detections.router, prefix="/api")
    app.include_router(video_jobs.router, prefix="/api")
    app.include_router(count_jobs.router, prefix="/api")
    app.include_router(enrichment_jobs.router, prefix="/api")

    @app.middleware("http")
    async def request_identity(request: Request, call_next) -> Response:
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.middleware("http")
    async def video_upload_authentication(request: Request, call_next) -> Response:
        return await reject_unauthorized_video_upload(request, call_next, settings)

    def documented_openapi():
        if app.openapi_schema is None:
            schema=get_openapi(title=app.title,version=app.version,routes=app.routes,description=app.description)
            metadata=PlatePreviewMetadata.model_json_schema(ref_template="#/components/schemas/{model}")
            definitions=metadata.pop("$defs",{})
            schema.setdefault("components",{}).setdefault("schemas",{}).update(definitions)
            schema["components"]["schemas"]["PlatePreviewMetadata"]=metadata
            app.openapi_schema=schema
        return app.openapi_schema
    app.openapi=documented_openapi
    return app


app = create_app()
