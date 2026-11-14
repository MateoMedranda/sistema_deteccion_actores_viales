from __future__ import annotations

from pathlib import Path
from fastapi import UploadFile

from app.api.error_handlers import ApiError
from app.adapters.video_probe import FFprobeAdapter
from app.core.config import Settings
from app.domain.models import VideoMetadata


class VideoValidator:
    def __init__(self, settings: Settings, probe: FFprobeAdapter) -> None:
        self.settings, self.probe = settings, probe

    async def stage_and_validate(self, upload: UploadFile, path: Path) -> VideoMetadata:
        if upload.content_type != "video/mp4" or Path(upload.filename or "").suffix.lower() != ".mp4":
            raise ApiError(415, "unsupported_video", "Only MP4 videos are allowed.")
        size = 0
        with path.open("wb") as output:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > self.settings.max_video_upload_bytes:
                    output.close(); path.unlink(missing_ok=True)
                    raise ApiError(413, "file_too_large", "The video exceeds the configured size limit.")
                output.write(chunk)
        metadata = self.probe.probe(path, size)
        invalid = (metadata.codec != "h264" or "mp4" not in metadata.container or metadata.duration_seconds <= 0 or metadata.duration_seconds > self.settings.max_video_duration_seconds or metadata.width > self.settings.max_video_width or metadata.height > self.settings.max_video_height or metadata.fps > self.settings.max_video_fps or metadata.total_frames <= 0 or metadata.total_frames > self.settings.max_video_frames)
        if invalid:
            path.unlink(missing_ok=True)
            raise ApiError(415, "unsupported_video", "The video does not meet the configured profile.")
        return metadata
