from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator, model_validator
from app.core.paths import BACKEND_ROOT, backend_path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_ROOT / ".env", extra="ignore")

    @model_validator(mode="after")
    def resolve_backend_paths(self) -> "Settings":
        for name in (
            "model_weights_path", "ultralytics_path", "temp_artifact_dir",
            "video_job_db_path", "video_temp_dir", "count_job_db_path", "count_temp_dir",
            "attribute_model_weights_path", "attribute_model_manifest_path",
            "plate_model_weights_path", "enrichment_job_db_path", "enrichment_temp_dir",
        ):
            value = getattr(self, name)
            if value is not None:
                setattr(self, name, backend_path(value))
        return self

    model_weights_path: Path | None = None
    ultralytics_path: Path | None = None
    api_key: str | None = None
    api_keys: str | None = None
    model_confidence_threshold: float = Field(default=0.25, ge=0, le=1)
    inference_device: str = "0"
    torch_num_threads: int | None = Field(default=None, ge=1)
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    max_image_pixels: int = Field(default=16_000_000, gt=0)
    artifact_ttl_seconds: int = Field(default=900, gt=0)
    max_concurrent_inferences: int = Field(default=1, gt=0)
    temp_artifact_dir: Path = Path(".runtime/artifacts")
    max_video_upload_bytes: int = Field(default=100 * 1024 * 1024, gt=0)
    max_video_duration_seconds: int = Field(default=120, gt=0)
    max_video_width: int = Field(default=1920, gt=0)
    max_video_height: int = Field(default=1080, gt=0)
    max_video_fps: int = Field(default=30, gt=0)
    max_video_frames: int = Field(default=3600, gt=0)
    video_detection_interval: int = Field(default=1, ge=1, le=2)
    video_progressive_batch_frames: int = Field(default=15,ge=1,le=60)
    video_progressive_batch_seconds: float = Field(default=.5,gt=0,le=10)
    video_progressive_buffer_seconds: float = Field(default=5,gt=0,le=30)
    max_concurrent_video_jobs: int = Field(default=1, gt=0)
    max_queued_video_jobs: int = Field(default=20, gt=0)
    video_job_timeout_seconds: int = Field(default=300, gt=0)
    video_result_ttl_seconds: int = Field(default=3600, gt=0)
    video_job_db_path: Path = Path(".runtime/video-jobs.sqlite3")
    video_temp_dir: Path = Path(".runtime/video-jobs")
    max_concurrent_count_jobs: int = Field(default=1, gt=0)
    max_queued_count_jobs: int = Field(default=20, gt=0)
    count_result_ttl_seconds: int = Field(default=3600, gt=0)
    count_job_db_path: Path = Path(".runtime/count-jobs.sqlite3")
    count_temp_dir: Path = Path(".runtime/count-jobs")
    ffprobe_executable: str = "ffprobe"
    ffmpeg_executable: str = "ffmpeg"
    attribute_model_weights_path: Path | None = None
    attribute_model_manifest_path: Path | None = None
    plate_model_weights_path: Path | None = None
    paddle_ocr_lang: str = "en"
    enrichment_result_ttl_seconds: int = Field(default=900, gt=0)
    enrichment_job_db_path: Path = Path(".runtime/enrichment-jobs.sqlite3")
    enrichment_temp_dir: Path = Path(".runtime/enrichment")
    max_concurrent_enrichment_jobs: int = Field(default=1, gt=0)
    max_queued_enrichment_jobs: int = Field(default=20, gt=0)
    max_concurrent_attribute_inferences: int = Field(default=1, gt=0)
    max_concurrent_plate_inferences: int = Field(default=1, gt=0)
    vehicle_classes: str = "car,truck,bus,van,pickup,suv,sedan,hatchback,mpv,estate"
    max_evidence_frames_per_track: int = Field(default=3, ge=1, le=20)
    plate_localizer_threshold: float = Field(default=0.25, ge=0, le=1)
    plate_ocr_retry_threshold: float = Field(default=0.70, ge=0, le=1)
    plate_ocr_accept_threshold: float = Field(default=0.80, ge=0, le=1)
    frontend_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    video_inspection_max_queued: int = Field(default=20, gt=0)
    video_inspection_max_contexts_per_job: int = Field(default=128, gt=0)
    video_inspection_max_bytes_per_job: int = Field(default=134217728, gt=0)
    video_inspection_max_resource_bytes: int = Field(default=8388608, gt=0)
    video_inspection_decode_max_frames: int = Field(default=300, gt=0)
    video_inspection_decode_timeout_seconds: float = Field(default=5, gt=0)

    @model_validator(mode="after")
    def inspection_limits(self):
        if self.video_inspection_max_resource_bytes > self.video_inspection_max_bytes_per_job:
            raise ValueError("Inspection resource limit exceeds job quota")
        return self

    def vehicle_class_set(self) -> set[str]:
        return {item.strip().lower() for item in self.vehicle_classes.split(",") if item.strip()}

    def frontend_origin_list(self) -> list[str]:
        origins = [item.strip().rstrip("/") for item in self.frontend_allowed_origins.split(",") if item.strip()]
        if any(origin == "*" for origin in origins):
            raise ValueError("FRONTEND_ALLOWED_ORIGINS cannot contain wildcard origins")
        if any(not origin.startswith(("http://", "https://")) for origin in origins):
            raise ValueError("FRONTEND_ALLOWED_ORIGINS entries must be HTTP(S) origins")
        return origins

    @field_validator("api_key")
    @classmethod
    def api_key_is_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("API_KEY cannot be blank")
        return value

    def runtime_errors(self) -> list[str]:
        errors: list[str] = []
        if self.model_weights_path is None:
            errors.append("MODEL_WEIGHTS_PATH is required")
        elif not self.model_weights_path.is_file():
            errors.append("MODEL_WEIGHTS_PATH does not exist")
        if self.api_key is None and not self.api_keys:
            errors.append("API_KEY or API_KEYS is required")
        return errors

    def configured_api_keys(self) -> dict[str, str]:
        """Return key-id to secret mappings without ever logging the secret values.

        `API_KEY` preserves the first iteration contract.  `API_KEYS` allows comma-separated
        `principal_id:secret` values for isolated video jobs.
        """
        keys: dict[str, str] = {}
        if self.api_key:
            keys["default"] = self.api_key
        if self.api_keys:
            for item in self.api_keys.split(","):
                key_id, separator, secret = item.strip().partition(":")
                if not separator or not key_id or not secret:
                    raise ValueError("API_KEYS entries must use principal_id:secret")
                keys[key_id] = secret
        return keys
