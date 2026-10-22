from __future__ import annotations

from typing import Protocol

import numpy as np

from app.domain.models import Detection


class Detector(Protocol):
    def detect(self, image: np.ndarray) -> list[Detection]: ...


class ReadyDetector(Detector, Protocol):
    @property
    def model_name(self) -> str: ...
