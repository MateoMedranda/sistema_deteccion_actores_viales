"""Frozen boundaries; fixture material establishes no detector/OCR accuracy."""
import hashlib,json
from pathlib import Path
def test_renderer_reference_is_frozen():
    root=Path(__file__).resolve().parents[2]
    baseline=json.loads((root/"specs/008-exploracion-imagen-video/baseline.json").read_text())
    assert hashlib.sha256((root/"tests/fixtures/video_presentation/legacy_renderer.py").read_bytes()).hexdigest()==baseline["renderer_sha256"]
def test_public_contract_keeps_previous_receipts():
    from app.domain.schemas import VideoJobAccepted,EnrichmentJobAccepted
    assert "job_id" in VideoJobAccepted.model_fields
    assert "enrichment_job_id" in EnrichmentJobAccepted.model_fields
