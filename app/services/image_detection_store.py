from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.api.error_handlers import ApiError
from app.domain.models import Detection
from app.services.source_artifacts import SourceArtifactStore


@dataclass(frozen=True)
class ImageDetectionSource:
    source_id: str
    owner_key_id: str
    original_path: Path
    width: int
    height: int
    media_type: str
    detections: tuple[Detection, ...]
    expires_at: datetime


class ImageDetectionStore:
    def __init__(self, artifacts: SourceArtifactStore, ttl_seconds: int) -> None:
        self.artifacts = artifacts
        self.ttl = timedelta(seconds=ttl_seconds)
        self._sources: dict[str, ImageDetectionSource] = {}
        self._expired: set[tuple[str, str]] = set()
        self._lock = threading.RLock()

    def create(self, source_id: str, owner_key_id: str, image: bytes, media_type: str,
               width: int, height: int, detections: list[Detection]) -> ImageDetectionSource:
        with self._lock:
            self.cleanup()
            suffix = ".png" if media_type == "image/png" else ".jpg"
            source = ImageDetectionSource(source_id, owner_key_id, self.artifacts.save(image, suffix), width,
                height, media_type, tuple(detections), datetime.now(UTC) + self.ttl)
            self._sources[source_id] = source
            return source

    def get(self, source_id: str, owner_key_id: str) -> ImageDetectionSource:
        with self._lock:
            self.cleanup()
            source = self._sources.get(source_id)
            if source is None or source.owner_key_id != owner_key_id:
                if (source_id, owner_key_id) in self._expired:
                    raise ApiError(410, "source_expired", "The requested source has expired.")
                raise ApiError(404, "source_not_found", "No accessible source was found.")
            return source

    def cleanup(self) -> None:
        with self._lock:
            now = datetime.now(UTC)
            for source_id, source in list(self._sources.items()):
                if source.expires_at <= now:
                    self.artifacts.remove(source.original_path)
                    self._expired.add((source_id, source.owner_key_id))
                    del self._sources[source_id]
