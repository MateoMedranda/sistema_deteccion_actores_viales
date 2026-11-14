from __future__ import annotations

from pathlib import Path
from uuid import uuid4


class VideoArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.input_root = root / "input"
        self.output_root = root / "output"
        self.input_root.mkdir(parents=True, exist_ok=True)
        self.output_root.mkdir(parents=True, exist_ok=True)

    def staged_input_path(self) -> Path:
        return self.input_root / f"{uuid4().hex}.mp4"

    def annotated_output_path(self) -> Path:
        return self.output_root / f"{uuid4().hex}.mp4"

    def remove(self, path: Path | None) -> None:
        if path is not None:
            path.unlink(missing_ok=True)

    def close(self) -> None:
        for root in (self.input_root, self.output_root):
            for path in root.glob("*"):
                path.unlink(missing_ok=True)
