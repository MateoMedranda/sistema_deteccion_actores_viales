from io import BytesIO

import pytest
from fastapi import UploadFile

from app.api.error_handlers import ApiError
from app.core.config import Settings
from app.domain.models import VideoMetadata
from app.services.video_validation import VideoValidator
from tests.video_fixtures import FakeProbe


def upload(data: bytes, content_type: str = "video/mp4") -> UploadFile:
    return UploadFile(BytesIO(data), filename="road.mp4", headers={"content-type": content_type})


@pytest.mark.asyncio
async def test_validation_stages_verified_mp4(tmp_path) -> None:
    settings = Settings(api_key="secret", max_video_upload_bytes=20, model_weights_path=None)
    metadata = await VideoValidator(settings, FakeProbe()).stage_and_validate(upload(b"video"), tmp_path / "video.mp4")
    assert metadata.codec == "h264"


@pytest.mark.asyncio
async def test_validation_rejects_oversized_or_wrong_codec(tmp_path) -> None:
    settings = Settings(api_key="secret", max_video_upload_bytes=3, model_weights_path=None)
    with pytest.raises(ApiError) as too_large:
        await VideoValidator(settings, FakeProbe()).stage_and_validate(upload(b"toolong"), tmp_path / "large.mp4")
    assert too_large.value.status_code == 413
    bad = VideoMetadata("video/mp4", "mp4", "hevc", 1, 1, 10, 10, 1, 1)
    with pytest.raises(ApiError) as wrong_codec:
        await VideoValidator(Settings(api_key="secret", model_weights_path=None), FakeProbe(bad)).stage_and_validate(upload(b"x"), tmp_path / "bad.mp4")
    assert wrong_codec.value.status_code == 415
