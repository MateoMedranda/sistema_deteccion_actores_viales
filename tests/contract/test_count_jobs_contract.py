from pathlib import Path


def test_count_contract_declares_schemas_and_routes() -> None:
    contract = Path("specs/003-conteo-por-linea/contracts/openapi.yaml").read_text(encoding="utf-8")
    for value in ("/v1/video-jobs/{videoJobId}/count-jobs:", "/v1/count-jobs/{countJobId}:", "CountJobCreateRequest", "CountEventPage"):
        assert value in contract


def test_runtime_openapi_documents_count_routes(client) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/video-jobs/{videoJobId}/count-jobs" in paths
    assert "/api/v1/count-jobs/{countJobId}" in paths
