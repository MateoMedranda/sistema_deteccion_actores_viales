from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PlateCandidate:
    text: str
    ocr_confidence: float
    localizer_confidence: float
    quality: float
    frame_index: int | None


def consensus(candidates: list[PlateCandidate], acceptance_threshold: float) -> PlateCandidate | None:
    """Accept only identical observed strings with sufficient weighted evidence."""
    buckets: dict[str, list[PlateCandidate]] = {}
    for candidate in candidates:
        if candidate.text and candidate.ocr_confidence >= acceptance_threshold:
            buckets.setdefault(candidate.text, []).append(candidate)
    if not buckets: return None
    ranked = sorted(buckets.values(), key=lambda values: sum(v.ocr_confidence * v.localizer_confidence * v.quality for v in values), reverse=True)
    if len(ranked) > 1 and len(ranked[0]) == len(ranked[1]): return None
    return max(ranked[0], key=lambda item: item.ocr_confidence * item.localizer_confidence * item.quality)
