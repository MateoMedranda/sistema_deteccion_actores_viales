from app.web.main import create_web_app
from app.web.settings import WebSettings

app = create_web_app(
    WebSettings(
        _env_file=None,
        backend_url="http://127.0.0.1:9415",
        backend_api_key="controlled-009",
        origin="http://127.0.0.1:9413",
    )
)
