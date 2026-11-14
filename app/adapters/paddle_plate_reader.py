from __future__ import annotations
import numpy as np
from app.adapters.plate_reader_protocol import PlateReading


class PaddlePlateReader:
    def __init__(self, language: str = "en") -> None:
        from paddleocr import PaddleOCR
        self.ocr = PaddleOCR(use_angle_cls=True, lang=language)

    def read(self, plate_crop: np.ndarray) -> PlateReading | None:
        result = self.ocr.ocr(plate_crop, cls=True)
        if not result or not result[0]: return None
        lines = result[0]
        text = "".join(str(line[1][0]) for line in lines).replace(" ", "").upper()
        scores = [float(line[1][1]) for line in lines]
        return PlateReading(text, sum(scores) / len(scores)) if text and scores else None
