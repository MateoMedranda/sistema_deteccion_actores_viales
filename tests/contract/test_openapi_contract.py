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


def test_generated_openapi_matches_counting_routes_and_security():
    documented = yaml.safe_load(
        Path("specs/003-conteo-por-linea/contracts/openapi.yaml").read_text(encoding="utf-8")
    )
    generated = create_app(Settings(api_key="test"), FakeDetector()).openapi()
    for path in documented["paths"]:
        assert f"/api{path}" in generated["paths"]
    created = generated["paths"]["/api/v1/video-jobs/{videoJobId}/count-jobs"]["post"]
    assert created["security"] == [{"ApiKeyAuth": []}]


def test_006_operations_expose_required_extensions_and_capabilities():
    generated = create_app(Settings(_env_file=None, api_key="test"), FakeDetector()).openapi()
    paths = generated["paths"]
    assert "/api/v1/detections/{requestId}/original-image" in paths
    response = generated["components"]["schemas"]["DetectionResponse"]
    assert {"original_image", "source_expires_at"} <= set(response["required"])
    assert "enrichment_eligible" in generated["components"]["schemas"]["DetectionResponseItem"]["required"]
    health = paths["/health/enrichment-ready"]["get"]["responses"]
    assert {"200", "503"} <= set(health)
    schema = generated["components"]["schemas"]["EnrichmentReadinessResponse"]
    assert "capabilities" in schema["required"]
    documented = yaml.safe_load(Path("specs/006-mejoras-frontend/contracts/openapi-additions.yaml").read_text(encoding="utf-8"))
    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "$ref":
                    target = documented
                    assert value.startswith("#/")
                    for segment in value[2:].split("/"):
                        target = target[segment.replace("~1", "/").replace("~0", "~")]
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
    walk(documented)
    assert set(documented["paths"]) <= set(paths)
