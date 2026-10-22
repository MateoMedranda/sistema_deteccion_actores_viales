from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.api.error_handlers import ApiError
from app.core.config import Settings
from app.domain.models import ValidatedImage


ALLOWED_MEDIA_TYPES = {"image/jpeg", "image/png"}
ALLOWED_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


class ImageValidator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def validate(self, upload: UploadFile) -> ValidatedImage:
        if upload.content_type not in ALLOWED_MEDIA_TYPES:
            raise ApiError(415, "unsupported_media_type", "Only JPEG and PNG images are allowed.")
        extension = Path(upload.filename or "").suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise ApiError(415, "unsupported_extension", "Only .jpg, .jpeg, and .png filenames are allowed.")

        chunks: list[bytes] = []
        total = 0
        while chunk := await upload.read(1024 * 1024):
            total += len(chunk)
            if total > self.settings.max_upload_bytes:
                raise ApiError(413, "file_too_large", "The image exceeds the configured size limit.")
            chunks.append(chunk)
        data = b"".join(chunks)
        if not data:
            raise ApiError(400, "missing_image", "An image file is required.")

        try:
            with Image.open(BytesIO(data)) as probe:
                image_format = probe.format
                width, height = probe.size
                probe.verify()
            with Image.open(BytesIO(data)) as decoded:
                decoded.load()
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise ApiError(422, "undecodable_image", "The image cannot be decoded safely.") from exc

        media_type = ALLOWED_FORMATS.get(image_format or "")
        if media_type is None or media_type != upload.content_type:
            raise ApiError(415, "unsupported_media_type", "Only valid JPEG and PNG images are allowed.")
        if media_type == "image/jpeg" and extension not in {".jpg", ".jpeg"}:
            raise ApiError(415, "unsupported_extension", "The filename extension does not match the image format.")
        if media_type == "image/png" and extension != ".png":
            raise ApiError(415, "unsupported_extension", "The filename extension does not match the image format.")
        if width * height > self.settings.max_image_pixels:
            raise ApiError(413, "image_too_large", "The image dimensions exceed the configured limit.")

        return ValidatedImage(
            data=data,
            media_type=media_type,
            width=width,
            height=height,
            original_filename=upload.filename,
        )
