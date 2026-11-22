"""UI gateway entry point. This process never imports app.main or loads models."""
from __future__ import annotations
import asyncio,json,logging,secrets
from contextlib import asynccontextmanager,suppress
from urllib.parse import urlsplit
import httpx
from fastapi import FastAPI,Request
from starlette.responses import JSONResponse,Response
from starlette.staticfiles import StaticFiles
from app.web.settings import WebSettings
from app.web.sessions import SessionStore
from app.web.proxy import Proxy,RelayError,classify,limited_json,safe_error
from time import monotonic

def create_web_app(settings:WebSettings|None=None,*,transport=None,clock=None):
    invalid=False
    if settings is None:
        try:settings=WebSettings()
        except Exception:
            settings=WebSettings.model_construct();invalid=True
    sessions=SessionStore(settings.session_ttl_seconds,settings.max_sessions,clock)
    @asynccontextmanager
    async def lifespan(app):
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        async with httpx.AsyncClient(transport=transport,trust_env=False,verify=True,follow_redirects=False,
          timeout=httpx.Timeout(30,connect=2,pool=.05),limits=httpx.Limits(max_connections=16,max_keepalive_connections=8)) as client:
            app.state.proxy=Proxy(settings,sessions,client)
            async def cleanup():
                while True:sessions.cleanup();await asyncio.sleep(1)
            task=asyncio.create_task(cleanup())
            try:yield
            finally:
                task.cancel()
                with suppress(asyncio.CancelledError):await task
                sessions.close()
    app=FastAPI(lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)
    app.state.sessions=sessions
    @app.exception_handler(RelayError)
    async def expected_error(request,error):return safe_error(error.status,error.code)
    def guard(request,*,javascript=False,mutation=False):
        if request.headers.get("host","").lower()!=urlsplit(settings.origin).netloc.lower():raise RelayError(403,"web_host_rejected")
        if request.headers.get("sec-fetch-site") in ("cross-site","same-site"):raise RelayError(403,"web_origin_rejected")
        if mutation and request.headers.get("origin")!=settings.origin.rstrip("/"):raise RelayError(403,"web_origin_rejected")
        if javascript and request.headers.get("x-ui-request")!="1":raise RelayError(403,"web_request_rejected")
    def context(request,*,native=False):
        guard(request,javascript=not native,mutation=request.method not in ("GET","HEAD"))
        token=request.cookies.get("road_ui_session");session=sessions.get(token)
        if not session:raise RelayError(401,"web_session_expired")
        if not native and not secrets.compare_digest(request.headers.get("x-ui-csrf",""),session.csrf):raise RelayError(403,"web_csrf_rejected")
        return session,token
    @app.get("/health/live")
    async def health():return {"status":"alive"}
    @app.post("/web/session")
    async def bootstrap(request:Request):
        guard(request,javascript=True,mutation=True)
        body=bytearray()
        async for block in request.stream():
            body.extend(block)
            if len(body)>16384:raise RelayError(413,"web_body_too_large")
        try:
            if json.loads(body)!= {}:raise ValueError()
        except ValueError:raise RelayError(422,"web_json_invalid")
        error="configuration_invalid" if invalid else settings.configuration_error()
        policy=None
        if not error:
            try:
                proxy=app.state.proxy
                async with asyncio.timeout(15):
                    response=await proxy.client.send(proxy.client.build_request("GET",settings.backend_url.rstrip("/")+"/api/v1/web-policy",headers={"X-API-Key":settings.backend_api_key.get_secret_value(),"Accept-Encoding":"identity"}),stream=True)
                    try:
                        if response.status_code==401:error="access_rejected"
                        elif response.status_code!=200:error="upstream_unavailable"
                        else:
                            from app.domain.schemas import WebPolicy
                            policy=WebPolicy.model_validate(await limited_json(response,monotonic()+15)).model_dump()
                    finally:await response.aclose()
            except Exception:error="upstream_unavailable"
        if error:return JSONResponse({"status":error,"code":"web_"+error,"message":"La conexión del servicio no está disponible."},status_code=401 if error=="access_rejected" else 503,headers={"Cache-Control":"no-store"})
        try:token,session=sessions.create(policy)
        except OverflowError:return safe_error(429,"web_capacity",{"Retry-After":"1"})
        result=JSONResponse({"status":"ready","epoch":session.epoch,"expires_at":session.expires_at.isoformat(),"csrf_token":session.csrf,"policy":policy},headers={"Cache-Control":"no-store"})
        result.set_cookie("road_ui_session",token,httponly=True,secure=settings.origin.startswith("https:"),samesite="strict",path="/",max_age=settings.session_ttl_seconds)
        return result
    @app.delete("/web/session")
    async def reset(request:Request):
        _,token=context(request);sessions.remove(token)
        result=Response(status_code=204,headers={"Cache-Control":"no-store"})
        result.delete_cookie("road_ui_session",path="/",secure=settings.origin.startswith("https:"),httponly=True,samesite="strict")
        return result
    @app.api_route("/web-api/{suffix:path}",methods=["GET","POST","DELETE","PUT","PATCH","HEAD","OPTIONS"])
    async def relay(request:Request,suffix:str):
        kind=classify(request.method,"/"+suffix,request.scope["raw_path"],request.query_params)
        session,token=context(request,native=kind=="native")
        return await app.state.proxy.handle(request,session,token,kind)
    if settings.static_dir.is_dir():app.mount("/",StaticFiles(directory=settings.static_dir,html=True),name="frontend")
    return app

app=create_web_app()
