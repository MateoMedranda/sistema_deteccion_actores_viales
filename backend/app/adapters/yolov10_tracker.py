from __future__ import annotations

import numpy as np
from app.domain.models import Detection

class YOLOv10ByteTrackAdapter:
    """Own ByteTrack state per video, sharing only the detector weights.

    Model.track registers callbacks capturing the first persist flag. Passing False
    for the first still frame reset those callbacks on every subsequent prediction,
    recycling identities. Raw prediction plus an owned tracker avoids that reset
    and prevents image predictions from advancing a video's tracking state.
    """
    def __init__(self, model, confidence_threshold: float, device: str) -> None:
        self._model=model
        self._confidence_threshold=confidence_threshold
        self._device=device
        self.reset()

    def reset(self) -> None:
        self._tracker=None

    def track(self, frame: np.ndarray) -> list[tuple[Detection,int]]:
        if self._tracker is None:
            from ultralytics.trackers.byte_tracker import BYTETracker
            from ultralytics.utils import YAML, IterableSimpleNamespace
            from ultralytics.utils.checks import check_yaml
            self._tracker=BYTETracker(args=IterableSimpleNamespace(**YAML.load(check_yaml("bytetrack.yaml"))))
        result=self._model.predict(frame,conf=self._confidence_threshold,device=self._device,verbose=False,mode="predict")[0]
        tracks=self._tracker.update(result.boxes.cpu().numpy(),result.orig_img)
        output=[]
        height,width=frame.shape[:2]
        for row in tracks:
            # Kalman predictions may extend outside the frame when a vehicle leaves.
            # Match Results.update's clipping without mutating the tracker's state.
            x1,y1,x2,y2=map(int,row[:4])
            x1,x2=max(0,min(width,x1)),max(0,min(width,x2))
            y1,y2=max(0,min(height,y1)),max(0,min(height,y2))
            if x2<=x1 or y2<=y1:
                continue
            tid=int(row[4]);score=float(row[5]);cls=int(row[6])
            output.append((Detection(cls,str(self._model.names[cls]),score,x1,y1,x2,y2),tid))
        return output
