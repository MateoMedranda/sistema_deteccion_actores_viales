import pytest
from starlette.datastructures import QueryParams
from app.web.proxy import classify, RelayError


@pytest.mark.parametrize(
    "method,path,query,kind",
    [
        ("POST", "/api/v1/video-jobs", "presentation=progressive", "video-upload"),
        ("HEAD", "/api/v1/video-jobs/a/playback/source", "", "progressive-source"),
        (
            "GET",
            "/api/v1/video-jobs/a/playback/frames",
            "from_us=0&to_us=5000000&snapshot=0",
            "json",
        ),
        (
            "GET",
            "/api/v1/video-jobs/a/playback/tracks/12/evidence/12345678-1234-1234-1234-123456789012/vehicle",
            "",
            "progressive-evidence",
        ),
    ],
)
def test_closed_allowlist(method, path, query, kind):
    assert classify(method, path, path.encode(), QueryParams(query)) == kind


@pytest.mark.parametrize(
    "query",
    [
        "from_us=-1",
        "snapshot=9007199254740992",
        "cursor=x&cursor=y",
        "url=http://foreign",
        "from_us=1.2",
    ],
)
def test_invalid_window_query(query):
    with pytest.raises(RelayError):
        classify(
            "GET",
            "/api/v1/video-jobs/a/playback/frames",
            b"/api/v1/video-jobs/a/playback/frames",
            QueryParams(query),
        )
