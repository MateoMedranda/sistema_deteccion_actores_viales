from __future__ import annotations

from collections import Counter
from pathlib import Path

import cv2

from app.domain.models import CountEvent, CountJob, FrameDetection


class CountAnnotationService:
    """Renders count evidence using an already annotated source video; never calls inference."""

    def render(
        self,
        job: CountJob,
        source_path: Path,
        destination: Path,
        detections: list[FrameDetection],
        events: list[CountEvent],
    ) -> None:
        capture = cv2.VideoCapture(str(source_path))
        if not capture.isOpened():
            raise RuntimeError("count_source_artifact_missing")
        width, height = job.total_frames and int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
        writer = cv2.VideoWriter(str(destination), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
        if not writer.isOpened():
            capture.release()
            raise RuntimeError("count_output_initialization_failed")
        events_by_frame: dict[int, list[CountEvent]] = {}
        for event in events:
            events_by_frame.setdefault(event.frame_index, []).append(event)
        totals: Counter[tuple[str, str]] = Counter()
        frame_index = 0
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                for event in events_by_frame.get(frame_index, []):
                    totals[(event.class_name, event.direction)] += 1
                start = (round(job.line.point_a.x * width), round(job.line.point_a.y * height))
                end = (round(job.line.point_b.x * width), round(job.line.point_b.y * height))
                cv2.line(frame, start, end, (0, 215, 255), 2, cv2.LINE_AA)
                cv2.putText(frame, "A_to_B / B_to_A", (12, 24), cv2.FONT_HERSHEY_SIMPLEX, .55, (0, 215, 255), 2, cv2.LINE_AA)
                for offset, ((class_name, count_direction), total) in enumerate(sorted(totals.items())):
                    cv2.putText(
                        frame, f"{class_name} {count_direction}: {total}", (12, 48 + offset * 22),
                        cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 215, 255), 1, cv2.LINE_AA,
                    )
                writer.write(frame)
                frame_index += 1
        finally:
            capture.release()
            writer.release()
