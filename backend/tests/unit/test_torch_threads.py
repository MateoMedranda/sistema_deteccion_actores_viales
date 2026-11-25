from types import SimpleNamespace
import json
import logging

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.torch_threads import TorchThreadPolicy
from app.core.logging import JsonFormatter
from tests.unit.test_video_profile import profile
from app.services.video_profile import render_report


class FakeTorch:
    def __init__(self):
        self.intraop = 8
        self.writes = []

    def get_num_threads(self):
        return self.intraop

    def get_num_interop_threads(self):
        return 8

    def set_num_threads(self, value):
        self.writes.append(value)
        self.intraop = value


def test_config_default_and_explicit_environment(tmp_path, monkeypatch):
    monkeypatch.delenv("TORCH_NUM_THREADS", raising=False)
    assert Settings(_env_file=None).torch_num_threads is None
    env = tmp_path / ".env"
    env.write_text("TORCH_NUM_THREADS=16", encoding="utf-8")
    assert Settings(_env_file=env).torch_num_threads == 16
    monkeypatch.setenv("TORCH_NUM_THREADS", "4")
    assert Settings(_env_file=env).torch_num_threads == 4


@pytest.mark.parametrize("value", [0, -1, "invalid", 1.5])
def test_invalid_thread_configuration_is_rejected(value):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, torch_num_threads=value)


def test_explicit_policy_survives_lazy_ultralytics_reset_and_does_not_repeat_setter():
    torch = FakeTorch()
    policy = TorchThreadPolicy(16, torch_module=torch)
    assert torch.writes == [16]
    callbacks = {}
    model = SimpleNamespace(add_callback=lambda key, value: callbacks.update({key: value}))
    policy.bind_yolo(model)
    # Simulate CPU selection inside lazy predictor setup.
    torch.intraop = 8
    callbacks["on_predict_start"](object())
    assert policy.snapshot()["effective_intraop"] == 16
    callbacks["on_predict_start"](object())
    assert torch.writes == [16, 16]
    assert policy.snapshot()["effective_interop"] == 8


def test_unconfigured_policy_keeps_native_defaults_without_hooks():
    torch = FakeTorch()
    policy = TorchThreadPolicy(None, torch_module=torch)
    policy.bind_yolo(object())
    policy.apply()
    assert torch.writes == []


def test_detector_passes_policy_to_image_predictor_and_video_tracker(monkeypatch, tmp_path):
    import ultralytics
    from app.adapters.yolov10_detector import YOLOv10Detector
    callbacks = {}
    model = SimpleNamespace(add_callback=lambda key, value: callbacks.update({key: value}))
    monkeypatch.setattr(ultralytics, "YOLO", lambda path: model)
    policy = TorchThreadPolicy(4, torch_module=FakeTorch())
    detector = YOLOv10Detector(tmp_path / "model.pt", .25, "cpu", thread_policy=policy)
    assert "on_predict_start" in callbacks
    tracker = detector.create_video_tracker()
    assert tracker._model is model
    assert tracker._thread_policy is policy
    assert tracker.detection_interval == 1


def test_effective_thread_samples_are_bounded_and_old_reports_still_render(tmp_path):
    p = profile(tmp_path)
    for value in (4, 4, 8):
        p.record_cpu_threads(dict(requested_intraop=4, effective_intraop=value,
                                 effective_interop=8, logical_cpus=16))
    data = p.snapshot()
    assert data["cpu_threads"]["observed_detection_calls"] == 3
    assert data["cpu_threads"]["min_intraop"] == 4
    assert data["cpu_threads"]["max_intraop"] == 8
    assert data["cpu_threads"]["mismatched_calls"] == 1
    assert "solicitados/efectivos: 4/8" in render_report(data)
    del data["cpu_threads"]
    assert "Hilos CPU" not in render_report(data)
    json.dumps(data, allow_nan=False)


def test_structured_log_includes_thread_settings_without_private_data():
    torch = FakeTorch()
    record = logging.LogRecord("test", logging.INFO, "", 0, "torch_cpu_threads", (), None)
    for key, value in TorchThreadPolicy(4, torch_module=torch).snapshot().items():
        setattr(record, key, value)
    payload = json.loads(JsonFormatter().format(record))
    assert payload["requested_intraop"] == payload["effective_intraop"] == 4
    assert payload["effective_interop"] == 8


def test_real_torch_inference_in_worker_respects_policy_after_native_reset():
    from concurrent.futures import ThreadPoolExecutor
    import torch
    previous = torch.get_num_threads()
    policy = TorchThreadPolicy(2)
    def execute():
        torch.set_num_threads(8)
        policy.apply(object())
        result = torch.mm(torch.ones(4, 4), torch.ones(4, 4))
        return policy.snapshot(), result.tolist()
    try:
        with ThreadPoolExecutor(max_workers=1) as worker:
            state, result = worker.submit(execute).result()
        assert state["effective_intraop"] == 2
        assert result == [[4.] * 4] * 4
    finally:
        torch.set_num_threads(previous)
