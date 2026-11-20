from __future__ import annotations
import os
import threading
from unittest.mock import patch
import numpy as np
from app.adapters.plate_reader_protocol import PlateReading

_initialization_lock = threading.Lock()


def _cpu_predictor(factory, config):
    # PaddleOCR 2.x forces switch_ir_optim(True) internally and doesn't call
    # disable_mkldnn() when its flag is False. Paddle 3.3 enables it by default.
    config.disable_mkldnn()
    config.switch_ir_optim(False)
    config.enable_new_ir(False)
    return factory(config)


class PaddlePlateReader:
    def __init__(self, language: str = "en") -> None:
        # Match the evaluated Windows pipeline. Load Torch's DLLs before Paddle's
        # and disable the legacy OCR graph optimizations that fuse broken oneDNN ops.
        import torch  # noqa: F401
        os.environ["FLAGS_use_mkldnn"] = "0"
        os.environ["FLAGS_enable_mkldnn"] = "0"
        from paddleocr import PaddleOCR
        from paddle import inference
        # Scope the compatibility hook to initialization; restore the factory
        # before returning, including when construction fails.
        with _initialization_lock:
            factory = inference.create_predictor
            with patch.object(inference, "create_predictor",
                              side_effect=lambda config: _cpu_predictor(factory, config)):
                self.ocr = PaddleOCR(use_angle_cls=True, lang=language, use_gpu=False,
                                     enable_mkldnn=False, ir_optim=False, show_log=False)
        self._lock = threading.Lock()

    def read(self, plate_crop: np.ndarray) -> PlateReading | None:
        # A Paddle predictor owns mutable buffers and cannot serve parallel calls.
        with self._lock:
            result = self.ocr.ocr(np.ascontiguousarray(plate_crop), cls=True)
        if not result or not result[0]: return None
        lines = result[0]
        text = "".join(str(line[1][0]) for line in lines).replace(" ", "").upper()
        scores = [float(line[1][1]) for line in lines]
        return PlateReading(text, sum(scores) / len(scores)) if text and scores else None
