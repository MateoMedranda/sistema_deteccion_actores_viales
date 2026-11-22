from app.core.config import Settings


def test_video_defaults_are_conservative() -> None:
    settings = Settings(api_key="test-key", model_weights_path=None)
    assert settings.max_video_upload_bytes == 104857600
    assert settings.max_video_duration_seconds == 120
    assert (settings.max_video_width, settings.max_video_height) == (1920, 1080)
    assert settings.max_video_fps == 30
    assert settings.max_video_frames == 3600
    assert settings.max_concurrent_video_jobs == 1
    assert settings.video_job_timeout_seconds == 300
    assert settings.video_result_ttl_seconds == 3600
