import cv2
import numpy as np

from app.domain.models import Detection
from app.services import annotation_service


def test_annotation_returns_jpeg_with_box_and_label(monkeypatch):
    image = np.zeros((50, 50, 3), dtype=np.uint8)
    labels: list[str] = []
    original_put_text = annotation_service.cv2.putText

    def record_label(*args, **kwargs):
        labels.append(args[1])
        return original_put_text(*args, **kwargs)

    monkeypatch.setattr(annotation_service.cv2, "putText", record_label)
    result = annotation_service.annotate(image, [Detection(0, "Car", 0.9, 5, 5, 35, 35)])
    decoded = cv2.imdecode(np.frombuffer(result, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert decoded is not None
    assert decoded.shape == image.shape
    assert np.any(decoded != 0)
    assert labels == ["Car 0.90"]
