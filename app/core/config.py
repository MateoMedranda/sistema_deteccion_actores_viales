from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    model_weights_path: Path | None = None
    ultralytics_path: Path | None = None
    api_key: str | None = None
    model_confidence_threshold: float = Field(default=0.25, ge=0, le=1)
    inference_device: str = "0"
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    max_image_pixels: int = Field(default=16_000_000, gt=0)
    artifact_ttl_seconds: int = Field(default=900, gt=0)
    max_concurrent_inferences: int = Field(default=1, gt=0)
    temp_artifact_dir: Path = Path(".runtime/artifacts")

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
        if self.api_key is None:
            errors.append("API_KEY is required")
        return errors
