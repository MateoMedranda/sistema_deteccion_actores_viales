from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
import numpy as np


@dataclass(frozen=True)
class PlateLocation:
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    confidence: float


class PlateLocalizer(Protocol):
    def locate(self, vehicle_crop: np.ndarray) -> PlateLocation | None: ...
