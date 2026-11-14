from pathlib import Path


def test_video_contract_declares_required_job_routes() -> None:
    contract = Path("specs/002-procesamiento-video-vial/contracts/openapi.yaml").read_text(encoding="utf-8")
    for route in ("/v1/video-jobs:", "/v1/video-jobs/{jobId}:", "/v1/video-jobs/{jobId}/detections:"):
        assert route in contract
    for status in ("'202'", "'401'", "'413'", "'415'", "'422'", "'503'"):
        assert status in contract


def test_runtime_openapi_documents_video_routes(client) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/video-jobs" in paths
    assert "post" in paths["/api/v1/video-jobs"]
