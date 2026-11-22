from __future__ import annotations

import secrets
from dataclasses import dataclass

from fastapi import Request, Security
from fastapi.security import APIKeyHeader

from app.api.error_handlers import ApiError
from app.core.config import Settings


api_key_header = APIKeyHeader(
    name="X-API-Key", auto_error=False, scheme_name="ApiKeyAuth"
)


@dataclass(frozen=True)
class Principal:
    key_id: str


def authenticate_api_key(settings: Settings, supplied_key: str | None) -> Principal:
    configured = settings.configured_api_keys()
    if not configured:
        raise ApiError(503, "service_not_configured", "The analysis service is not configured.")
    if not supplied_key:
        raise ApiError(401, "unauthorized", "A valid API key is required.")
    matched: str | None = None
    # Compare every configured secret to avoid revealing which principal matched by timing.
    for key_id, secret in configured.items():
        if secrets.compare_digest(supplied_key, secret):
            matched = key_id
    if matched is None:
        raise ApiError(401, "unauthorized", "A valid API key is required.")
    return Principal(matched)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def require_api_key(
    request: Request,
    x_api_key: str | None = Security(api_key_header),
) -> Principal:
    settings: Settings = request.app.state.settings
    return authenticate_api_key(settings, x_api_key)
