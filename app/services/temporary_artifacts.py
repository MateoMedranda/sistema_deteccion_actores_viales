from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock
from uuid import uuid4

from app.domain.models import TemporaryArtifact


class TemporaryArtifactStore:
    def __init__(self, root: Path, ttl_seconds: int) -> None:
        self.root = root
        self.ttl = timedelta(seconds=ttl_seconds)
        self._artifacts: dict[str, TemporaryArtifact] = {}
        self._expired: set[str] = set()
        self._lock = Lock()
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, request_id: str, image_bytes: bytes) -> TemporaryArtifact:
        with self._lock:
            self._cleanup_unlocked()
            artifact = TemporaryArtifact(
                request_id=request_id,
                path=self.root / f"{uuid4().hex}.jpg",
                expires_at=datetime.now(UTC) + self.ttl,
            )
            artifact.path.write_bytes(image_bytes)
            self._artifacts[request_id] = artifact
            return artifact

    def get(self, request_id: str) -> tuple[TemporaryArtifact | None, bool]:
        with self._lock:
            self._cleanup_unlocked()
            return self._artifacts.get(request_id), request_id in self._expired

    def cleanup(self) -> None:
        with self._lock:
            self._cleanup_unlocked()

    def _cleanup_unlocked(self) -> None:
        now = datetime.now(UTC)
        for request_id, artifact in list(self._artifacts.items()):
            if artifact.expires_at <= now:
                artifact.path.unlink(missing_ok=True)
                del self._artifacts[request_id]
                self._expired.add(request_id)

    def close(self) -> None:
        with self._lock:
            for artifact in self._artifacts.values():
                artifact.path.unlink(missing_ok=True)
            self._artifacts.clear()
