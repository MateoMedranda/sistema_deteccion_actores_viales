from __future__ import annotations

from app.core.config import Settings


def test_cors_allows_configured_vite_origin(client) -> None:
    response = client.options(
        "/api/v1/detections/images",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-API-Key,Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "x-api-key" in response.headers["access-control-allow-headers"].lower()


def test_cors_rejects_unconfigured_origin(client) -> None:
    response = client.options(
        "/api/v1/detections/images",
        headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "POST"},
    )
    assert response.headers.get("access-control-allow-origin") is None


def test_cors_configuration_rejects_wildcard() -> None:
    settings = Settings(api_key="key", frontend_allowed_origins="*")
    try:
        settings.frontend_origin_list()
    except ValueError as error:
        assert "wildcard" in str(error)
    else:
        raise AssertionError("Wildcard origins must be rejected")
