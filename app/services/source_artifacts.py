from __future__ import annotations

from pathlib import Path
from uuid import uuid4


class SourceArtifactStore:
    """Private files used only while a source/result has not expired."""

    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def save(self, data: bytes, suffix: str = ".bin") -> Path:
        path = self.root / f"{uuid4().hex}{suffix}"
        path.write_bytes(data)
        return path

    def remove(self, path: Path | None) -> None:
        if path is not None:
            path.unlink(missing_ok=True)

    def close(self) -> None:
        for path in self.root.glob("*"):
            if path.is_file():
                path.unlink(missing_ok=True)
