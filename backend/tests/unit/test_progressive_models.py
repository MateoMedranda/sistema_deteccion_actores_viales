from fractions import Fraction
import cv2
import pytest
from app.adapters.timed_video_decoder import TimedVideoDecoder
from tests.fixtures_progressive import video


def test_decoder_preserves_vfr_intervals_and_pixels(tmp_path):
    path = video(
        tmp_path / "vfr.mp4", [Fraction(0), Fraction(1, 10), Fraction(3, 10), Fraction(2, 5)]
    )
    frames = list(TimedVideoDecoder(path))
    assert len(frames) == 4
    assert [f.start_us for f in frames] == [0, 100000, 300000, 400000]
    assert all(a.end_us == b.start_us for a, b in zip(frames, frames[1:]))
    capture = cv2.VideoCapture(str(path))
    for frame in frames:
        ok, reference = capture.read()
        assert ok and (reference == frame.image).all()
    capture.release()
