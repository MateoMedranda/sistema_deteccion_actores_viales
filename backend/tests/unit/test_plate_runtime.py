from types import SimpleNamespace
from unittest.mock import Mock
import logging

import numpy as np
import pytest

from app.adapters.paddle_plate_reader import _cpu_predictor
from app.adapters.yolov8_plate_localizer import YOLOv8PlateLocalizer
from app.services.enrichment_processing import EnrichmentProcessor
from tests.enrichment_fixtures import FakeAttributes, FakeLocalizer, FakeReader


def test_cpu_predictor_disables_incompatible_optimizations_before_creation():
    config = Mock()
    def create(received):
        assert received is config
        config.disable_mkldnn.assert_called_once_with()
        config.switch_ir_optim.assert_called_once_with(False)
        config.enable_new_ir.assert_called_once_with(False)
        return "predictor"
    assert _cpu_predictor(create, config) == "predictor"


def test_plate_threshold_is_forwarded_to_yolo():
    adapter = YOLOv8PlateLocalizer.__new__(YOLOv8PlateLocalizer)
    adapter.threshold = .1
    box = SimpleNamespace(conf=[.15], xyxy=np.array([[1, 2, 15, 8]]))
    adapter.model = Mock(return_value=[SimpleNamespace(boxes=[box])])
    image = np.zeros((20, 30, 3), dtype=np.uint8)
    assert adapter.locate(image).confidence == .15
    assert adapter.model.call_args.kwargs["conf"] == .1


def test_ocr_failure_preserves_localization_and_logs_no_sensitive_values(caplog, monkeypatch):
    monkeypatch.setattr(logging.getLogger("road_actor_detection"), "propagate", True)
    reader = FakeReader()
    reader.read = Mock(side_effect=RuntimeError("SECRET_PLATE_AND_PATH"))
    processor = EnrichmentProcessor(FakeAttributes(), FakeLocalizer(), reader, .7, .8)
    attributes, plate = processor.enrich(np.zeros((20, 30, 3), dtype=np.uint8))
    assert attributes["status"] == "completed"
    assert plate["status"] == "failed"
    assert plate["localizer_confidence"] == .95
    assert plate["bbox_relative"]["x_min"] == pytest.approx(2 / 30)
    assert plate["error_code"] == "plate_processing_failed"
    record = next(r for r in caplog.records if r.message == "plate_processing_failed")
    assert record.branch == "ocr" and record.exception_type == "RuntimeError"
    assert "SECRET_PLATE_AND_PATH" not in caplog.text


def test_successful_ocr_returns_observed_text():
    processor = EnrichmentProcessor(FakeAttributes(), FakeLocalizer(), FakeReader(), .7, .8)
    _, plate = processor.enrich(np.zeros((20, 30, 3), dtype=np.uint8))
    assert plate["status"] == "read" and plate["text"] == "SYN123"
