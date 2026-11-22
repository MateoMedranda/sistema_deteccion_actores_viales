from __future__ import annotations
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import RLock
from uuid import uuid4
from app.domain.models import TemporaryArtifact
from app.api.error_handlers import ApiError
from app.services.managed_image_files import ManagedImageFiles

class TemporaryArtifactStore:
    def __init__(self, root: Path, ttl_seconds: int, clock=None):
        self.root, self.ttl = root, timedelta(seconds=ttl_seconds)
        self.clock = clock or (lambda: datetime.now(UTC))
        self._artifacts: dict[str, TemporaryArtifact] = {}
        self._expired: set[str] = set()
        self._owners: dict[str, str | None] = {}
        self._lock = RLock()
        self.root.mkdir(parents=True, exist_ok=True)
        self.files = ManagedImageFiles(self.root,"annotation",self.clock)

    def save(self, request_id, image_bytes, owner_key_id=None, expires_at=None):
        with self._lock:
            self._cleanup_unlocked()
            expiry = min(expires_at,self.clock()+self.ttl) if expires_at else self.clock()+self.ttl
            path = self.files.save(image_bytes,".jpg",expiry)
            artifact = TemporaryArtifact(request_id,path,expiry,owner_key_id)
            self._artifacts[request_id] = artifact
            self._owners[request_id] = owner_key_id
            return artifact

    def get(self, request_id):
        with self._lock:
            self._cleanup_unlocked()
            return self._artifacts.get(request_id), request_id in self._expired

    def read(self, request_id, owner_key_id):
        with self._lock:
            artifact, expired = self.get(request_id)
            if artifact is None:
                if expired and self._owners.get(request_id) == owner_key_id:
                    raise ApiError(410, "artifact_expired", "The annotated image has expired.")
                raise ApiError(404, "artifact_not_found", "No accessible image was found.")
            if artifact.owner_key_id != owner_key_id:
                raise ApiError(404, "artifact_not_found", "No accessible image was found.")
            return artifact.path.read_bytes()

    def cleanup(self):
        with self._lock:
            self._cleanup_unlocked()

    def _cleanup_unlocked(self):
        self.files.cleanup(self.clock())
        for request_id, artifact in list(self._artifacts.items()):
            if artifact.expires_at <= self.clock():
                self.files.remove(artifact.path)
                self._expired.add(request_id)
                del self._artifacts[request_id]

    def close(self):
        with self._lock:
            for artifact in self._artifacts.values():
                self.files.remove(artifact.path)
            self._artifacts.clear()
