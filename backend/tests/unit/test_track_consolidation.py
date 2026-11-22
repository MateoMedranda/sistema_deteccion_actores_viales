from __future__ import annotations

from app.services.track_consolidation import select_track_evidence
from tests.enrichment_fixtures import TRACK_DETECTIONS


def test_track_consolidation_returns_one_unit_and_bounded_evidence() -> None:
    units = select_track_evidence(TRACK_DETECTIONS, {"car"}, 1)
    assert len(units) == 1
    assert units[0]["track_id"] == 1 and len(units[0]["evidence"]) == 1
    assert units[0]["frame_index"] == 1
