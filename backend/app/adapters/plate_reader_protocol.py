from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
import numpy as np


@dataclass(frozen=True)
class PlateReading:
    text: str
    confidence: float


class PlateReader(Protocol):
    def read(self, plate_crop: np.ndarray) -> PlateReading | None: ...
