import pytest

from app.api.dependencies import authenticate_api_key
from app.api.error_handlers import ApiError
from app.core.config import Settings


def test_legacy_key_maps_to_default_principal() -> None:
    settings = Settings(api_key="secret", model_weights_path=None)
    assert authenticate_api_key(settings, "secret").key_id == "default"


def test_invalid_key_has_safe_error() -> None:
    settings = Settings(api_key="secret", model_weights_path=None)
    with pytest.raises(ApiError) as error:
        authenticate_api_key(settings, "wrong")
    assert error.value.status_code == 401
    assert "secret" not in error.value.message


def test_multiple_principals_are_mapped_without_exposing_secrets() -> None:
    settings = Settings(api_keys="north:secret-a,south:secret-b", model_weights_path=None)
    assert authenticate_api_key(settings, "secret-a").key_id == "north"
    assert authenticate_api_key(settings, "secret-b").key_id == "south"
