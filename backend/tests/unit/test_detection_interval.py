from types import SimpleNamespace
import numpy as np
import pytest
import torch
from ultralytics.engine.results import Boxes
from app.adapters.yolov10_tracker import YOLOv10ByteTrackAdapter
from app.core.config import Settings


class MovingModel:
    names = {0: "Car", 1: "Truck"}

    def __init__(self):
        self.calls = []

    def predict(self, frame, **kwargs):
        index = round(int(frame[0, 0, 0]) / 12)
        self.calls.append(index)
        car = [5 + 2 * index, 6, 17 + 2 * index, 18, .95, 0]
        truck = [42, 25, 60, 40, .94, 1]
        rows = [car, truck] if len(self.calls) % 2 else [truck, car]
        return [SimpleNamespace(boxes=Boxes(torch.tensor(rows), frame.shape[:2]), orig_img=frame)]


def image(index):
    return np.full((48, 64, 3), index * 12, np.uint8)


def test_alternate_prediction_retains_ids_advances_motion_and_halves_yolo_calls():
    model = MovingModel()
    tracker = YOLOv10ByteTrackAdapter(model, .25, "cpu")
    tracker.set_detection_interval(2)
    ids, centers, predicted = {}, [], []
    for index in range(12):
        pairs = tracker.track(image(index))
        assert tracker.last_was_detection == (index % 2 == 0)
        predicted.append(not tracker.last_was_detection)
        assert len(pairs) == 2
        for detection, tid in pairs:
            assert ids.setdefault(detection.class_name, tid) == tid
            assert 0 <= detection.x_min < detection.x_max <= 64
            if detection.class_name == "Car":
                centers.append((detection.x_min + detection.x_max) / 2)
    assert model.calls == [0, 2, 4, 6, 8, 10]
    assert sum(predicted) == 6
    assert centers[5] > centers[4]  # prediction moves, rather than repeating a rectangle
    assert tracker._tracker.frame_id == 12  # Kalman advances once per SOURCE frame


def test_prediction_does_not_turn_missing_measurements_into_lost_tracks():
    tracker = YOLOv10ByteTrackAdapter(MovingModel(), .25, "cpu")
    tracker.set_detection_interval(2)
    first = tracker.track(image(0))
    second = tracker.track(image(1))
    assert [tid for _, tid in first] == [tid for _, tid in second]
    assert not tracker._tracker.lost_stracks
    assert all(track.frame_id == 1 for track in tracker._tracker.tracked_stracks)
    tracker.track(image(2))
    assert all(track.frame_id == 3 for track in tracker._tracker.tracked_stracks)


def test_interval_one_preserves_existing_adapter_and_reset_restarts_cadence():
    model = MovingModel()
    tracker = YOLOv10ByteTrackAdapter(model, .25, "cpu")
    for index in range(4):
        tracker.track(image(index))
    assert model.calls == [0, 1, 2, 3]
    with pytest.raises(ValueError):
        tracker.set_detection_interval(2)
    tracker.reset()
    tracker.set_detection_interval(2)
    model.calls.clear()
    before = tracker.track(image(0))
    tracker.track(image(1))
    tracker.reset()
    model.calls.clear()
    assert before == tracker.track(image(0))
    assert tracker.last_was_detection


@pytest.mark.parametrize("interval", [0, -1, 3, 1.5])
def test_invalid_interval_is_rejected(interval):
    with pytest.raises(ValueError):
        Settings(_env_file=None, video_detection_interval=interval)


def test_interval_can_be_configured_from_environment(monkeypatch):
    monkeypatch.setenv("VIDEO_DETECTION_INTERVAL", "2")
    assert Settings(_env_file=None).video_detection_interval == 2


def test_lost_tracks_are_not_presented_as_predictions():
    tracker = YOLOv10ByteTrackAdapter(MovingModel(), .25, "cpu")
    tracker.set_detection_interval(2)
    tracker.track(image(0))
    missing = tracker._tracker.tracked_stracks.pop()
    missing.mark_lost()
    tracker._tracker.lost_stracks.append(missing)
    assert missing.track_id not in [tid for _, tid in tracker.track(image(1))]
    assert missing.frame_id == 1


def test_short_occlusion_reactivates_same_id_and_keeps_lost_tracks_hidden():
    model = MovingModel()
    predict = model.predict
    def occluded(frame, **kwargs):
        result = predict(frame, **kwargs)[0]
        if round(int(frame[0,0,0])/12) == 4:
            result.boxes = result.boxes[result.boxes.cls == 1]
        return [result]
    model.predict = occluded
    tracker = YOLOv10ByteTrackAdapter(model,.25,"cpu")
    tracker.set_detection_interval(2)
    first_id = None
    for index in range(8):
        cars = [tid for detection,tid in tracker.track(image(index)) if detection.class_name == "Car"]
        if index == 0:
            first_id = cars[0]
        if index in (4,5):
            assert not cars
        else:
            assert cars == [first_id]
    assert model.calls == [0,2,4,6]
