from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
import numpy as np


@dataclass(frozen=True)
class AttributePrediction:
    name: str
    label: str
    confidence: float


class AttributeExtractor(Protocol):
    def extract(self, vehicle_crop: np.ndarray) -> list[AttributePrediction]: ...
