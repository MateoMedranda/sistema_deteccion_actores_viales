from __future__ import annotations

import secrets

from fastapi import Request, Security
from fastapi.security import APIKeyHeader

from app.api.error_handlers import ApiError
from app.core.config import Settings


api_key_header = APIKeyHeader(
    name="X-API-Key", auto_error=False, scheme_name="ApiKeyAuth"
)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def require_api_key(
    request: Request,
    x_api_key: str | None = Security(api_key_header),
) -> None:
    settings: Settings = request.app.state.settings
    if not settings.api_key:
        raise ApiError(503, "service_not_configured", "The analysis service is not configured.")
    if not x_api_key or not secrets.compare_digest(x_api_key, settings.api_key):
        raise ApiError(401, "unauthorized", "A valid API key is required.")
