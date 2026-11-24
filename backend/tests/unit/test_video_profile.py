import json
import logging
from pathlib import Path
from types import SimpleNamespace
import pytest
from app.services.video_profile import VideoProfile, render_report


def profile(tmp_path, clock=lambda: 0):
    job = SimpleNamespace(job_id="synthetic-job", metadata=SimpleNamespace(
        width=1920, height=1080, fps=30, duration_seconds=2, total_frames=60))
    detector = SimpleNamespace(model_name="model.pt", _device="cpu", _confidence_threshold=.25)
    return VideoProfile(job, detector, tmp_path, clock)


def test_accounting_separates_wait_tracking_encode_and_unmeasured_time(tmp_path):
    now = [0.0]
    p = profile(tmp_path, lambda: now[0])
    for stage, seconds in (("decode", .012), ("resource_wait", .030), ("detection", .040),
                           ("tracking", .008), ("publication", .004)):
        with p.measure(stage):
            now[0] += seconds
    now[0] += .006
    p.frames = 2
    p.confirmed(2, 100000, .1)
    p.end_analysis(complete=True)
    with p.measure("final_encode"):
        now[0] += .020
    with p.measure("cleanup"):
        now[0] += .010
    data = p.snapshot()
    assert data["analysis_wall_ms"] == 100
    assert data["total_wall_ms"] == 130
    assert data["analysis_fps"] == 20
    assert data["confirmed_video_seconds_per_wall_second"] == 1
    assert data["other_analysis_ms"] == 6
    assert data["stages"]["detection"]["analysis_percent"] == 40
    assert data["stages"]["resource_wait"]["total_ms"] == 30
    assert data["stages"]["tracking"]["ms_per_processed_frame"] == 4
    assert data["stages"]["final_encode"]["analysis_percent"] is None
    assert data["first_publication_ms"] == pytest.approx(100)
    assert data["initial_buffer_available_ms"] == pytest.approx(100)
    text = render_report(data)
    assert "Deteccion YOLO" in text and "Conversion final" in text


def test_failed_stage_still_records_time_and_zero_frame_report_is_finite(tmp_path):
    now = [0.0]
    p = profile(tmp_path, lambda: now[0])
    with pytest.raises(RuntimeError):
        with p.measure("detection"):
            now[0] += .023
            raise RuntimeError("private message not captured")
    p.end_analysis()
    data = p.snapshot()
    assert data["stages"]["detection"]["total_ms"] == 23
    assert not data["analysis_complete"]
    assert data["stages"]["detection"]["ms_per_processed_frame"] is None
    assert "private" not in json.dumps(data, allow_nan=False)


def test_checkpoint_is_periodic_atomic_and_does_not_accumulate_samples(tmp_path):
    now = [0.0]
    p = profile(tmp_path, lambda: now[0])
    logger = logging.getLogger("profile-test")
    p.checkpoint(logger)
    assert not list(tmp_path.glob("*.json"))
    now[0] = 5
    p.frames = 10
    p.checkpoint(logger)
    assert json.loads((tmp_path / "synthetic-job.json").read_text())["processed_frames"] == 10
    now[0] = 10
    p.frames = 20
    p.checkpoint(logger)
    assert len(list(tmp_path.iterdir())) == 1
    assert json.loads((tmp_path / "synthetic-job.json").read_text())["processed_frames"] == 20
    assert not any(isinstance(value, list) for value in vars(p).values())


def test_report_write_failure_does_not_propagate_or_expose_exception(tmp_path, monkeypatch, caplog):
    p = profile(tmp_path)
    def denied(*args, **kwargs):
        raise PermissionError("PRIVATE_SOURCE_PLATE_SECRET")
    monkeypatch.setattr(Path, "write_text", denied)
    assert not p.save(logging.getLogger("profile-test"))
    assert "video_profile_write_failed" in caplog.text
    assert "PRIVATE_SOURCE_PLATE_SECRET" not in caplog.text


def test_profiled_tracker_keeps_identical_observations_and_separates_prediction(tmp_path):
    import numpy as np
    from tests.unit.test_tracker_identity import Detector
    from app.adapters.yolov10_tracker import YOLOv10ByteTrackAdapter
    p = profile(tmp_path)
    plain = YOLOv10ByteTrackAdapter(Detector(), .25, "cpu")
    measured = YOLOv10ByteTrackAdapter(Detector(), .25, "cpu")
    for i in range(8):
        frame = np.full((100, 180, 3), i, np.uint8)
        assert plain.track(frame) == measured.track_profiled(frame, p)
    assert p.stages["detection"]["calls"] == 8
    assert p.stages["tracking"]["calls"] == 9  # one initialization, eight associations
    assert p.stages["detection_tracking_combined"]["calls"] == 0


def test_tracker_timers_charge_prediction_and_association_to_different_stages(tmp_path):
    import numpy as np
    from tests.unit.test_tracker_identity import Detector
    from app.adapters.yolov10_tracker import YOLOv10ByteTrackAdapter
    now = [0.0]
    p = profile(tmp_path, lambda: now[0])
    model = Detector()
    predict = model.predict
    def timed_predict(*args, **kwargs):
        now[0] += .020
        return predict(*args, **kwargs)
    model.predict = timed_predict
    tracker = YOLOv10ByteTrackAdapter(model, .25, "cpu")
    def update(*args):
        now[0] += .005
        return np.array([[10,10,30,30,1,.9,0,0]], dtype=np.float32)
    tracker._tracker = SimpleNamespace(update=update)
    result = tracker.track_profiled(np.zeros((100,180,3), np.uint8), p)
    assert result[0][1] == 1
    assert p.stages["detection"]["total_ms"] == pytest.approx(20)
    assert p.stages["tracking"]["total_ms"] == pytest.approx(5)
    assert p.stages["resource_wait"]["total_ms"] == 0
