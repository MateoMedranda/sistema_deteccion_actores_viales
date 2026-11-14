from app.domain.models import Detection
from app.services.video_processing import IoUTracker


def test_fallback_tracker_keeps_positive_id_for_consecutive_frames() -> None:
    tracker = IoUTracker()
    first = Detection(0, "car", .9, 1, 1, 20, 20)
    second = Detection(0, "car", .9, 2, 1, 21, 20)
    assert tracker.assign([first]) == [1]
    assert tracker.assign([second]) == [1]


def test_fallback_tracker_resets_between_jobs() -> None:
    detection = Detection(0, "car", .9, 1, 1, 20, 20)
    assert IoUTracker().assign([detection]) == [1]
    assert IoUTracker().assign([detection]) == [1]
