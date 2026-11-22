"""Local synthetic gateway; key belongs only to the isolated upstream fixture."""
from app.web.main import create_web_app
from app.web.settings import WebSettings
app=create_web_app(WebSettings(_env_file=None,backend_url="http://127.0.0.1:8767",backend_api_key="ui-synthetic-key",origin="http://127.0.0.1:4173"))
