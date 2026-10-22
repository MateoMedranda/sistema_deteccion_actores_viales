import pytest
from fastapi import UploadFile

from app.api.error_handlers import ApiError
from app.core.config import Settings
from app.services.image_validation import ImageValidator
from tests.conftest import image_bytes


@pytest.mark.asyncio
async def test_accepts_valid_jpeg():
    upload = UploadFile(filename="street.jpg", file=__import__("io").BytesIO(image_bytes()), headers={"content-type": "image/jpeg"})
    result = await ImageValidator(Settings(api_key="test")).validate(upload)
    assert result.media_type == "image/jpeg"
    assert result.width == 40


@pytest.mark.asyncio
async def test_accepts_png_with_matching_extension():
    upload = UploadFile(filename="street.png", file=__import__("io").BytesIO(image_bytes("PNG")), headers={"content-type": "image/png"})
    result = await ImageValidator(Settings(api_key="test")).validate(upload)
    assert result.media_type == "image/png"


@pytest.mark.asyncio
async def test_rejects_filename_extension_that_does_not_match_the_image():
    upload = UploadFile(filename="street.png", file=__import__("io").BytesIO(image_bytes()), headers={"content-type": "image/jpeg"})
    with pytest.raises(ApiError) as error:
        await ImageValidator(Settings(api_key="test")).validate(upload)
    assert error.value.code == "unsupported_extension"


@pytest.mark.asyncio
async def test_rejects_unsupported_media_type():
    upload = UploadFile(filename="notes.txt", file=__import__("io").BytesIO(b"hello"), headers={"content-type": "text/plain"})
    with pytest.raises(ApiError) as error:
        await ImageValidator(Settings(api_key="test")).validate(upload)
    assert error.value.status_code == 415


@pytest.mark.asyncio
async def test_rejects_corrupt_image():
    upload = UploadFile(filename="bad.jpg", file=__import__("io").BytesIO(b"not an image"), headers={"content-type": "image/jpeg"})
    with pytest.raises(ApiError) as error:
        await ImageValidator(Settings(api_key="test")).validate(upload)
    assert error.value.status_code == 422


@pytest.mark.asyncio
async def test_rejects_file_above_limit():
    upload = UploadFile(filename="big.jpg", file=__import__("io").BytesIO(b"x" * 11), headers={"content-type": "image/jpeg"})
    with pytest.raises(ApiError) as error:
        await ImageValidator(Settings(api_key="test", max_upload_bytes=10)).validate(upload)
    assert error.value.status_code == 413


@pytest.mark.asyncio
async def test_rejects_image_above_pixel_limit():
    upload = UploadFile(filename="large.jpg", file=__import__("io").BytesIO(image_bytes(size=(20, 20))), headers={"content-type": "image/jpeg"})
    with pytest.raises(ApiError) as error:
        await ImageValidator(Settings(api_key="test", max_image_pixels=100)).validate(upload)
    assert error.value.status_code == 413
