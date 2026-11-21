from __future__ import annotations
import threading
from dataclasses import dataclass,replace
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
    def __init__(self, artifacts: SourceArtifactStore, ttl_seconds: int, clock=None):
        self.artifacts, self.ttl = artifacts, timedelta(seconds=ttl_seconds)
        self.clock = clock or (lambda: datetime.now(UTC))
        self._sources: dict[str, ImageDetectionSource] = {}
        self._expired: set[tuple[str, str]] = set()
        self._lock = threading.RLock()

    def create(self, source_id, owner_key_id, image, media_type, width, height, detections):
        with self._lock:
            self.cleanup()
            expiry=self.clock()+self.ttl
            source = ImageDetectionSource(source_id, owner_key_id,
                self.artifacts.save(image, ".png" if media_type == "image/png" else ".jpg", expires_at=expiry),
                width, height, media_type, tuple(detections), expiry)
            self._sources[source_id] = source
            return source

    def limit_expiry(self,source_id,expires_at):
        with self._lock:
            source=self._sources[source_id]
            updated=replace(source,expires_at=min(source.expires_at,expires_at))
            self.artifacts.limit_expiry(source.original_path,updated.expires_at)
            self._sources[source_id]=updated
            return updated

    def get(self, source_id, owner_key_id):
        with self._lock:
            self.cleanup()
            source = self._sources.get(source_id)
            if source is None or source.owner_key_id != owner_key_id:
                if (source_id, owner_key_id) in self._expired:
                    raise ApiError(410, "source_expired", "The requested source has expired.")
                raise ApiError(404, "source_not_found", "No accessible source was found.")
            return source

    def read_original(self, source_id, owner_key_id):
        with self._lock:
            source = self.get(source_id, owner_key_id)
            return source.original_path.read_bytes(), source

    def cleanup(self):
        with self._lock:
            now = self.clock()
            self.artifacts.cleanup(now)
            for source_id, source in list(self._sources.items()):
                if source.expires_at <= now:
                    self.artifacts.remove(source.original_path)
                    self._expired.add((source_id, source.owner_key_id))
                    del self._sources[source_id]
