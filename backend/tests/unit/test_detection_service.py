from app.domain.models import AnalysisStatus, Detection, ValidatedImage
from app.services.detection_service import DetectionService
from app.services.temporary_artifacts import TemporaryArtifactStore
from tests.conftest import FakeDetector, image_bytes


def test_detection_service_maps_box_and_confidence(tmp_path, caplog):
    service = DetectionService(
        FakeDetector([Detection(4, "Bus", 0.88, 1, 2, 20, 25)]),
        TemporaryArtifactStore(tmp_path, 30),
        __import__("logging").getLogger("test"),
    )
    result = service.analyze("request-1", ValidatedImage(image_bytes(), "image/jpeg", 40, 40, "x.jpg"))
    assert result.detections[0].confidence == 0.88
    assert result.detections[0].bbox.x_min == 1
    assert result.detections[0].bbox.y_max == 25
    assert result.annotated_image.url.endswith("request-1/annotated-image")
    state = service.request_state("request-1")
    assert state is not None
    assert state.status == AnalysisStatus.COMPLETED
    assert state.processing_time_ms is not None


def test_detection_service_clamps_bounding_boxes_to_image_limits(tmp_path):
    service = DetectionService(
        FakeDetector([Detection(4, "Bus", 0.88, -10, -4, 90, 70)]),
        TemporaryArtifactStore(tmp_path, 30),
        __import__("logging").getLogger("test"),
    )
    result = service.analyze("request-bounds", ValidatedImage(image_bytes(), "image/jpeg", 40, 40, "x.jpg"))
    assert result.detections[0].bbox.model_dump() == {
        "x_min": 0,
        "y_min": 0,
        "x_max": 40,
        "y_max": 40,
    }


def test_failed_inference_does_not_create_an_artifact(tmp_path):
    class FailingDetector:
        model_name = "failing.pt"

        def detect(self, image):
            raise RuntimeError("model failure")

    store = TemporaryArtifactStore(tmp_path, 30)
    service = DetectionService(FailingDetector(), store, __import__("logging").getLogger("test"))
    from app.api.error_handlers import ApiError
    import pytest

    with pytest.raises(ApiError) as error:
        service.analyze("request-failure", ValidatedImage(image_bytes(), "image/jpeg", 40, 40, "x.jpg"))
    assert error.value.status_code == 503
    assert store.get("request-failure") == (None, False)
    assert service.request_state("request-failure").status == AnalysisStatus.FAILED
