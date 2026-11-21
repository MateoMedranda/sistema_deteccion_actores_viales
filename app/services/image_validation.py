from __future__ import annotations
from io import BytesIO
from pathlib import Path
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from PIL import Image, ImageOps, UnidentifiedImageError
from app.api.error_handlers import ApiError
from app.core.config import Settings
from app.domain.models import ValidatedImage

ALLOWED_MEDIA_TYPES = {"image/jpeg", "image/png"}
ALLOWED_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

class ImageValidator:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def validate(self, upload: UploadFile) -> ValidatedImage:
        if upload.content_type not in ALLOWED_MEDIA_TYPES:
            raise ApiError(415, "unsupported_media_type", "Only JPEG and PNG images are allowed.")
        extension = Path(upload.filename or "").suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise ApiError(415, "unsupported_extension", "Only .jpg, .jpeg, and .png filenames are allowed.")
        chunks, total = [], 0
        while chunk := await upload.read(1024 * 1024):
            total += len(chunk)
            if total > self.settings.max_upload_bytes:
                raise ApiError(413, "file_too_large", "The image exceeds the configured size limit.")
            chunks.append(chunk)
        data = b"".join(chunks)
        if not data:
            raise ApiError(400, "missing_image", "An image file is required.")
        return await run_in_threadpool(self._normalize,data,upload.content_type,extension,upload.filename)

    def _normalize(self,data,content_type,extension,filename):
        try:
            with Image.open(BytesIO(data)) as probe:
                image_format = probe.format
                width, height = probe.size
                if width * height > self.settings.max_image_pixels:
                    raise ApiError(413, "image_too_large", "The image dimensions exceed the configured limit.")
                probe.verify()
            media_type = ALLOWED_FORMATS.get(image_format or "")
            if media_type is None or media_type != content_type:
                raise ApiError(415, "unsupported_media_type", "Only valid JPEG and PNG images are allowed.")
            if (media_type == "image/jpeg" and extension not in {".jpg", ".jpeg"}) or (media_type == "image/png" and extension != ".png"):
                raise ApiError(415, "unsupported_extension", "The filename extension does not match the image format.")
            with Image.open(BytesIO(data)) as decoded:
                decoded.load()
                canonical = ImageOps.exif_transpose(decoded).convert("RGB")
                # Recreate pixels so PNG metadata cannot inherit EXIF, GPS or text.
                clean = Image.frombytes("RGB", canonical.size, canonical.tobytes())
                output = BytesIO()
                clean.save(output, format="PNG")
                width, height = clean.size
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
            raise ApiError(422, "undecodable_image", "The image cannot be decoded safely.") from exc
        return ValidatedImage(output.getvalue(), "image/png", width, height, filename)
