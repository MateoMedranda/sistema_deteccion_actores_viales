import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from app.domain.progressive import PlaybackState, FramePage, TrackResult, Observation
from tests.integration.test_progressive_store import source
from app.services.video_progressive_store import ProgressiveStore


def test_additive_contract_preserves_required_nullable_fields(tmp_path):
    store = ProgressiveStore(tmp_path / "db")
    source(store, tmp_path / "source")
    value = store.snapshot("job-1", "owner")
    parsed = PlaybackState.model_validate(value)
    assert parsed.source is None and parsed.last_frame_start_us is None
    assert set(parsed.model_dump()) == set(value)
    value["revision"] = 2**53
    with pytest.raises(ValidationError):
        PlaybackState.model_validate(value)
    store.close()


def test_invalid_confidence_and_unknown_fields():
    ob = dict(
        ordinal=0,
        track_id=1,
        class_id=0,
        class_name="car",
        confidence=0.9,
        raw_bbox=dict(x_min=0, y_min=0, x_max=10, y_max=10),
        display_bbox=None,
    )
    for change in (
        {"confidence": float("nan")},
        {"confidence": 1.01},
        {"track_id": 0},
        {"private_path": "secret"},
    ):
        with pytest.raises(ValidationError):
            Observation.model_validate({**ob, **change})
