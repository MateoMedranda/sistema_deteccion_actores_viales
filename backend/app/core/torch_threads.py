"""One immutable CPU intra-op thread policy per API process.

Ultralytics resets CPU threads during lazy predictor setup. Its supported
on_predict_start callback runs after setup and before preprocessing/inference.
Reapply the same policy there, including for the optional plate predictor.
No predictor monkeypatching, inter-op changes, extra inference or worker pools.
"""
from __future__ import annotations

import os


class TorchThreadPolicy:
    def __init__(self, requested: int | None, logger=None, torch_module=None):
        if requested is not None and (type(requested) is not int or requested < 1):
            raise ValueError("torch_num_threads_must_be_positive")
        if torch_module is None:
            import torch as torch_module
        self.torch = torch_module
        self.requested = requested
        self.logger = logger
        self._logged = None
        self.apply()

    def snapshot(self):
        return {
            "requested_intraop": self.requested,
            "effective_intraop": self.torch.get_num_threads(),
            "effective_interop": self.torch.get_num_interop_threads(),
            "logical_cpus": os.cpu_count(),
        }

    def apply(self, predictor=None):
        if self.requested is not None and self.torch.get_num_threads() != self.requested:
            self.torch.set_num_threads(self.requested)
        state = self.snapshot()
        marker = (state["requested_intraop"], state["effective_intraop"])
        if self.logger is not None and marker != self._logged:
            self.logger.info("torch_cpu_threads", extra=state)
            self._logged = marker

    def bind_yolo(self, model):
        if self.requested is not None:
            model.add_callback("on_predict_start", self.apply)
