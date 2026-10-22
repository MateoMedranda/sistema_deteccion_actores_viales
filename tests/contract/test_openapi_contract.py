from pathlib import Path

import yaml

from app.core.config import Settings
from app.main import create_app
from tests.conftest import FakeDetector


def test_generated_openapi_matches_documented_routes_and_security():
    documented = yaml.safe_load(
        Path("specs/001-deteccion-imagen-vial/contracts/openapi.yaml").read_text(encoding="utf-8")
    )
    generated = create_app(Settings(api_key="test"), FakeDetector()).openapi()
    for path in documented["paths"]:
        assert f"/api{path}" in generated["paths"] or path.startswith("/health/")
    assert "ApiKeyAuth" in generated["components"]["securitySchemes"]
