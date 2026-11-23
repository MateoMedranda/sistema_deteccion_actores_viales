from tests.enrichment_fixtures import FakeAttributes, FakeReader, FakeLocalizer
from tests.conftest import FakeDetector, isolated_settings
from fastapi.testclient import TestClient
from app.main import create_app


def test_single_shared_models_and_orderly_progressive_shutdown(tmp_path, monkeypatch):
    counts = {"attributes": 0, "localizer": 0, "reader": 0}

    def factory(name, kind):
        def create(*args):
            counts[name] += 1
            return kind()

        return create

    for name, adapter, kind in (
        ("attributes", "EfficientNetAttributeExtractor", FakeAttributes),
        ("localizer", "YOLOv8PlateLocalizer", FakeLocalizer),
        ("reader", "PaddlePlateReader", FakeReader),
    ):
        monkeypatch.setattr("app.core.lifespan." + adapter, factory(name, kind))
    settings = isolated_settings(
        tmp_path,
        api_key="key",
        attribute_model_weights_path=tmp_path / "attrs",
        attribute_model_manifest_path=tmp_path / "manifest",
        plate_model_weights_path=tmp_path / "plate",
    )
    app = create_app(settings, FakeDetector())
    with TestClient(app):
        progressive = app.state.progressive_worker
        legacy = app.state.enrichment_worker
        assert (
            progressive.processor is legacy.processor is app.state.enrichment_job_service.processor
        )
        assert app.state.video_worker.processor.evidence is app.state.progressive_evidence
        assert app.state.video_worker.processor.progressive_inference_slots is progressive.slots
        assert progressive.thread.is_alive()
    assert not progressive.thread.is_alive()
    assert progressive.processor.executor._shutdown
    assert counts == {"attributes": 1, "localizer": 1, "reader": 1}
