from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from app.domain.models import Detection, VideoMetadata


class FakeProbe:
    def __init__(self, metadata: VideoMetadata | None = None) -> None:
        self.metadata = metadata or VideoMetadata("video/mp4", "mov,mp4,m4a,3gp,3g2,mj2", "h264", 1024, 1.0, 64, 48, 10.0, 10)

    def probe(self, path: Path, size_bytes: int) -> VideoMetadata:
        return VideoMetadata(
            self.metadata.media_type, self.metadata.container, self.metadata.codec, size_bytes,
            self.metadata.duration_seconds, self.metadata.width, self.metadata.height,
            self.metadata.fps, self.metadata.total_frames,
        )


class StableTrackerDetector:
    model_name = "fake-yolov10s.pt"

    def detect(self, image):
        return [Detection(0, "car", 0.9, 5, 5, min(30, image.shape[1]), min(30, image.shape[0]))]


def ffmpeg_executable() -> str:
    executable = shutil.which("ffmpeg")
    if not executable:
        pytest.skip("FFmpeg is not available in PATH")
    return executable


def make_h264_mp4(path: Path, duration: float = 1.0, fps: int = 10) -> Path:
    executable = ffmpeg_executable()
    subprocess.run(
        [executable, "-y", "-f", "lavfi", "-i", f"testsrc=size=64x48:rate={fps}", "-t", str(duration),
         "-pix_fmt", "yuv420p", "-c:v", "libx264", str(path)],
        check=True, capture_output=True,
    )
    return path
