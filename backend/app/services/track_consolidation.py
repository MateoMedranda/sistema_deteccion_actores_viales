from __future__ import annotations

from collections import defaultdict

from app.domain.models import FrameDetection


def select_track_evidence(detections: list[FrameDetection], vehicle_classes: set[str], maximum: int) -> list[dict]:
    """Return one public unit per track and bounded best-confidence evidence frames."""
    grouped: dict[int, list[FrameDetection]] = defaultdict(list)
    for item in detections:
        if item.class_name.lower() in vehicle_classes:
            grouped[item.track_id].append(item)
    units = []
    for detection_id, (track_id, values) in enumerate(sorted(grouped.items()), start=1):
        selected = sorted(values, key=lambda item: (-item.confidence, item.frame_index))[:maximum]
        primary = selected[0]
        units.append({"detection_id": detection_id, "track_id": track_id, "class_id": primary.class_id,
                      "class_name": primary.class_name, "frame_index": primary.frame_index,
                      "bbox": primary, "evidence": selected})
    return units
