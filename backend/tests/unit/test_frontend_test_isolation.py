def test_browser_server_isolates_all_temporary_stores():
    from tests.e2e.serve_frontend_test_api import settings,_path
    for name in ("temp_artifact_dir","video_job_db_path","video_temp_dir","count_job_db_path","count_temp_dir","enrichment_job_db_path","enrichment_temp_dir"):
        assert getattr(settings,name).resolve().is_relative_to(_path.resolve()), name
