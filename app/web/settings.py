from ipaddress import ip_address
from pathlib import Path
from urllib.parse import urlsplit
from pydantic import Field,SecretStr
from pydantic_settings import BaseSettings,SettingsConfigDict

def origin_valid(value:str)->bool:
    try:
        u=urlsplit(value)
        if u.scheme not in ("http","https") or not u.hostname or u.username or u.password or u.query or u.fragment or u.path not in ("","/") or any(c.isspace() for c in value):return False
        if u.port is not None and not 1<=u.port<=65535:return False
        if u.scheme=="https":return True
        try:return ip_address(u.hostname).is_loopback
        except ValueError:return u.hostname=="localhost"
    except ValueError:return False

class WebSettings(BaseSettings):
    model_config=SettingsConfigDict(env_prefix="WEB_",env_file=".env.web",extra="ignore")
    backend_url:str|None=None
    backend_api_key:SecretStr|None=None
    origin:str="http://127.0.0.1:4173"
    static_dir:Path=Path("frontend/dist")
    session_ttl_seconds:int=Field(default=900,ge=60,le=3600)
    max_sessions:int=Field(default=128,ge=1,le=1024)

    def configuration_error(self)->str|None:
        if not self.backend_url or not self.backend_api_key:return "configuration_missing"
        if not origin_valid(self.backend_url) or not origin_valid(self.origin):return "configuration_invalid"
        secret=self.backend_api_key.get_secret_value().strip()
        if not secret or secret.lower() in ("changeme","replace-me","your-api-key","placeholder"):return "configuration_invalid"
        return None
