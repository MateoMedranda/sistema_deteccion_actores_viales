from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Protocol

from app.api.error_handlers import ApiError
from app.domain.models import VideoMetadata


class VideoProbe(Protocol):
    def probe(self, path: Path, size_bytes: int) -> VideoMetadata: ...


class FFprobeAdapter(VideoProbe):
    def __init__(self, executable: str) -> None:
        self.executable = executable

    def probe(self, path: Path, size_bytes: int) -> VideoMetadata:
        try:
            completed = subprocess.run(
                [self.executable, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                capture_output=True, text=True, check=True, timeout=15,
            )
        except FileNotFoundError as exc:
            raise ApiError(503, "video_tools_unavailable", "Video processing is not available.") from exc
        except (subprocess.SubprocessError, OSError) as exc:
            raise ApiError(422, "invalid_video", "The video cannot be validated safely.") from exc
        data = json.loads(completed.stdout)
        stream = next((item for item in data.get("streams", []) if item.get("codec_type") == "video"), None)
        if stream is None:
            raise ApiError(422, "invalid_video", "The video cannot be validated safely.")
        numerator, _, denominator = str(stream.get("avg_frame_rate", "0/1")).partition("/")
        fps = float(numerator) / float(denominator or 1)
        return VideoMetadata(
            media_type="video/mp4",
            container=str(data.get("format", {}).get("format_name", "")),
            codec=str(stream.get("codec_name", "")),
            size_bytes=size_bytes,
            duration_seconds=float(data.get("format", {}).get("duration", 0)),
            width=int(stream.get("width", 0)), height=int(stream.get("height", 0)),
            fps=fps,
            total_frames=int(
                stream.get("nb_frames") or round(fps * float(data.get("format", {}).get("duration", 0)))
            ),
        )
