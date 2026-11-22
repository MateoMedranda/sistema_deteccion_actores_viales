from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.paths import BACKEND_ROOT, PROJECT_ROOT
from app.web.settings import WebSettings


@pytest.mark.parametrize("location", [PROJECT_ROOT, BACKEND_ROOT])
def test_configuration_paths_do_not_depend_on_working_directory(location, monkeypatch):
    monkeypatch.chdir(location)
    settings = Settings(_env_file=None, attribute_model_manifest_path="specs/004-extraccion-caracteristicas-y-placas/model-manifest.example.yaml")
    web = WebSettings(_env_file=None)
    assert settings.video_job_db_path == BACKEND_ROOT / ".runtime/video-jobs.sqlite3"
    assert settings.temp_artifact_dir == BACKEND_ROOT / ".runtime/artifacts"
    assert settings.attribute_model_manifest_path.is_file()
    assert web.static_dir == PROJECT_ROOT / "frontend/dist"


def test_explicit_absolute_storage_and_model_paths_are_preserved(tmp_path):
    settings = Settings(_env_file=None, video_temp_dir=tmp_path, model_weights_path=tmp_path / "model.pt")
    web = WebSettings(_env_file=None, static_dir=tmp_path)
    assert settings.video_temp_dir == tmp_path
    assert settings.model_weights_path == tmp_path / "model.pt"
    assert web.static_dir == tmp_path


def test_environment_file_locations_stay_in_backend():
    assert Path(Settings.model_config["env_file"]) == BACKEND_ROOT / ".env"
    assert Path(WebSettings.model_config["env_file"]) == BACKEND_ROOT / ".env.web"
