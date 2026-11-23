from fractions import Fraction
import subprocess
import cv2, numpy as np
import pytest
from app.adapters.timed_video_decoder import TimedVideoDecoder
from tests.fixtures_progressive import video


@pytest.mark.parametrize("kind", ["b-frames", "offset", "rotation"])
def test_timeline_matches_presentation_pixels(tmp_path, kind):
    original = video(tmp_path / "base.mp4", [Fraction(i, 30) for i in range(18)])
    target = tmp_path / (kind + ".mp4")
    if kind == "b-frames":
        args = ["-i", str(original), "-c:v", "libx264", "-bf", "2", "-crf", "0"]
    elif kind == "offset":
        args = ["-itsoffset", "1.25", "-i", str(original), "-c", "copy"]
    else:
        args = ["-i", str(original), "-c", "copy", "-metadata:s:v:0", "rotate=90"]
    subprocess.run(
        ["ffmpeg", "-nostdin", "-y", "-loglevel", "error", *args, str(target)],
        check=True,
        capture_output=True,
    )
    decoder = TimedVideoDecoder(target)
    frames = list(decoder)
    assert frames[0].start_us == 0
    assert len(frames) == 18
    assert all(a.end_us == b.start_us for a, b in zip(frames, frames[1:]))
    cap = cv2.VideoCapture(str(target))
    for frame in frames:
        ok, image = cap.read()
        assert ok and image.shape == frame.image.shape
        assert np.array_equal(image, frame.image)
    cap.release()
