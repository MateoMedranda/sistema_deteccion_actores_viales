"""Closed streaming relay. Backend authorization remains authoritative."""
from __future__ import annotations
import asyncio,json,re
from datetime import UTC,datetime
from time import monotonic
from uuid import UUID
import httpx
from starlette.responses import JSONResponse,Response,StreamingResponse

ID=r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}"
ROUTES=[
 ("GET|PUT|DELETE",rf"/api/v1/video-jobs/{ID}/playback/directed-count","json"),
 ("POST",rf"/api/v1/video-jobs/{ID}/playback/inspections","json"),
 ("GET",rf"/api/v1/video-jobs/{ID}/playback/inspections/[a-f0-9-]{{36}}","json"),
 ("GET",rf"/api/v1/video-jobs/{ID}/playback/inspections/[a-f0-9-]{{36}}/assets/[a-f0-9-]{{36}}/(?:vehicle|plate)","progressive-evidence"),
 ("GET",rf"/api/v1/video-jobs/{ID}/playback/inspections/[a-f0-9-]{{36}}/plate-preview","plate"),
 ("GET",rf"/api/v1/video-jobs/{ID}/playback/capabilities","json"),
 ("GET",r"/api/v1/web-policy","json"),
 ("GET",r"/health/(?:live|ready|video-ready|enrichment-ready|image-policy)","json"),
 ("POST",r"/api/v1/detections/images","image-upload"),
 ("GET",rf"/api/v1/detections/{ID}/(?:original-image|annotated-image)","image"),
 ("POST",r"/api/v1/video-jobs","video-upload"),
 ("GET|DELETE",rf"/api/v1/video-jobs/{ID}/playback","json"),
 ("POST",rf"/api/v1/video-jobs/{ID}/playback/tracks/[1-9][0-9]{{0,15}}/enrich","json"),
 ("GET|PUT|DELETE",rf"/api/v1/video-jobs/{ID}/playback/count","json"),
 ("GET|POST",rf"/api/v1/video-jobs/{ID}/playback/export","json"),
 ("GET|HEAD",rf"/api/v1/video-jobs/{ID}/playback/source","progressive-source"),
 ("GET",rf"/api/v1/video-jobs/{ID}/playback/(?:frames|tracks)","json"),
 ("GET",rf"/api/v1/video-jobs/{ID}/playback/tracks/[1-9][0-9]{{0,15}}","json"),
 ("GET",rf"/api/v1/video-jobs/{ID}/playback/tracks/[1-9][0-9]{{0,15}}/evidence/[a-f0-9-]{{36}}/(?:vehicle|plate)","progressive-evidence"),
 ("GET|DELETE",rf"/api/v1/video-jobs/{ID}","json"),
 ("GET",rf"/api/v1/video-jobs/{ID}/(?:detections|summary|annotated-video)","json"),
 ("GET",rf"/api/v1/video-jobs/{ID}/annotated-video/content","native"),
 ("POST",r"/api/v1/enrichment-jobs","enrich"),
 ("GET|DELETE",rf"/api/v1/enrichment-jobs/{ID}","json"),
 ("GET",rf"/api/v1/enrichment-jobs/{ID}/results","json"),
 ("GET",rf"/api/v1/enrichment-jobs/{ID}/detections/[1-9][0-9]*/plate-preview","plate"),
 ("POST",rf"/api/v1/video-jobs/{ID}/count-jobs","json"),
 ("GET|DELETE",rf"/api/v1/count-jobs/{ID}","json"),
 ("GET",rf"/api/v1/count-jobs/{ID}/events","json"),
 ("GET",rf"/api/v1/count-jobs/{ID}/annotated-video","native"),
]
def safe_error(status,code,headers=None):
    return JSONResponse({"code":code,"message":"No se pudo completar la solicitud."},status_code=status,headers={"Cache-Control":"no-store",**(headers or {})})
class RelayError(Exception):
    def __init__(self,status,code):self.status,self.code=status,code

def classify(method,path,raw_path,query):
    if b"%" in raw_path or "//" in path or ".." in path:raise RelayError(404,"web_route_invalid")
    kind=next((kind for verbs,pattern,kind in ROUTES if method in verbs.split("|") and re.fullmatch(pattern,path)),None)
    if not kind:raise RelayError(404,"web_route_invalid")
    pairs=list(query.multi_items());keys=[key for key,_ in pairs]
    if len(keys)!=len(set(keys)):raise RelayError(422,"web_query_invalid")
    allowed={"page","page_size"} if path.endswith(("/detections","/results","/events")) else {"profile"} if kind=="plate" else set()
    if kind=="video-upload":allowed={"presentation","enrichment"}
    elif path.endswith("/playback/directed-count"):allowed={"generation","at_us","revision"} if method=="GET" else {"generation","expected_revision"} if method=="DELETE" else set()
    elif path.endswith("/playback/count"):allowed={"at_us"} if method=="GET" else set()
    elif path.endswith("/playback/frames"):allowed={"from_us","to_us","snapshot","cursor"}
    elif path.endswith("/playback/tracks"):allowed={"snapshot","cursor"}
    if not set(keys)<=allowed:raise RelayError(422,"web_query_invalid")
    for key,value in pairs:
        if key=="generation":
            try:UUID(value)
            except ValueError:raise RelayError(422,"web_query_invalid")
        elif key=="enrichment":
            if value!="on-demand" or query.get("presentation")!="progressive":raise RelayError(422,"web_query_invalid")
        elif key=="presentation":
            if value!="progressive":raise RelayError(422,"web_query_invalid")
        elif key=="cursor":
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,512}",value):raise RelayError(422,"web_query_invalid")
        elif key in ("from_us","to_us","snapshot","at_us","revision","expected_revision"):
            if not re.fullmatch(r"(?:0|[1-9][0-9]{0,15})",value) or int(value)>2**53-1:raise RelayError(422,"web_query_invalid")
        elif key=="profile":
            if value!="display-contrast-v1":raise RelayError(422,"web_query_invalid")
        elif not re.fullmatch(r"[1-9][0-9]{0,8}",value) or (key=="page_size" and int(value)>100):raise RelayError(422,"web_query_invalid")
    return kind

async def limited_json(response,deadline):
    data=bytearray()
    async for block in response.aiter_bytes(65536):
        if monotonic()>=deadline:raise RelayError(504,"web_timeout")
        data.extend(block)
        if len(data)>2*1024*1024:raise RelayError(502,"web_response_too_large")
    try:return json.loads(data)
    except (ValueError,UnicodeError):raise RelayError(502,"web_invalid_response")

class Proxy:
    def __init__(self,settings,sessions,client):
        self.settings,self.sessions,self.client=settings,sessions,client
        self.active=0;self.uploads=0
    async def handle(self,request,session,token,kind):
        upload=kind.endswith("-upload")
        if self.active>=16 or (upload and self.uploads>=2):return safe_error(429,"web_capacity",{"Retry-After":"1"})
        self.active+=1
        if upload:self.uploads+=1
        owned=True;response=None
        def release():
            self.active-=1
            if upload:self.uploads-=1
        ttl=(session.expires_at-self.sessions.clock()).total_seconds()
        budget={"image-upload":120,"video-upload":180,"image":30,"plate":10,"native":60,"progressive-source":60,"progressive-evidence":30}.get(kind,10 if request.method=="GET" else 15)
        deadline=monotonic()+min(budget,ttl)
        path=request.url.path.removeprefix("/web-api")
        headers={"X-API-Key":self.settings.backend_api_key.get_secret_value(),"Accept-Encoding":"identity"}
        body=None
        try:
            if ttl<=0:raise RelayError(401,"web_session_expired")
            length=request.headers.get("content-length")
            if length and (not length.isdigit() or int(length)>2**40):raise RelayError(413,"web_body_too_large")
            if upload:
                content_type=request.headers.get("content-type","")
                if not content_type.lower().startswith("multipart/form-data;"):raise RelayError(422,"web_upload_invalid")
                maximum=session.policy["image" if kind=="image-upload" else "video"]["max_upload_bytes"]+65536
                headers["Content-Type"]=content_type
                if length and int(length)>maximum:raise RelayError(413,"web_body_too_large")
                async def bounded_input():
                    size=0
                    async for block in request.stream():
                        if not self.sessions.get(token) or monotonic()>=deadline:raise RelayError(401,"web_session_expired")
                        size+=len(block)
                        if size>maximum:raise RelayError(413,"web_body_too_large")
                        if monotonic()>=deadline or not self.sessions.get(token):raise RelayError(401,"web_session_expired")
                        for offset in range(0,len(block),65536):yield block[offset:offset+65536]
                body=bounded_input()
            else:
                data=bytearray()
                async with asyncio.timeout(max(.001,deadline-monotonic())):
                    async for block in request.stream():
                        if not self.sessions.get(token):raise RelayError(401,"web_session_expired")
                        data.extend(block)
                        if len(data)>(65536 if "/playback/inspections" in request.url.path or "/playback/directed-count" in request.url.path else 16384):raise RelayError(413,"web_body_too_large")
                if request.method in ("GET","HEAD","DELETE") and data:raise RelayError(422,"web_body_not_allowed")
                if data:
                    try:payload=json.loads(data)
                    except ValueError:raise RelayError(422,"web_json_invalid")
                    if not isinstance(payload,dict):raise RelayError(422,"web_json_invalid")
                    body=bytes(data);headers["Content-Type"]="application/json"
                else:payload={}
            is_video=kind=="video-upload" or (kind=="enrich" and isinstance(payload.get("source"),dict) and payload["source"].get("kind")=="video")
            intent=request.headers.get("x-ui-intent")
            if is_video and not intent:raise RelayError(422,"web_intent_required")
            if intent:
                try:intent=str(UUID(intent))
                except ValueError:raise RelayError(422,"web_intent_invalid")
                operation="video-upload" if kind=="video-upload" else "video-enrichment" if is_video else "image-enrichment"
                if is_video:
                    sequence=request.headers.get("x-ui-intent-generation")
                    if sequence is not None and not re.fullmatch(r"[1-9][0-9]{0,8}",sequence):raise RelayError(422,"web_intent_invalid")
                    generation=int(sequence) if sequence else None
                    prior=session.intents.get(operation)
                    if prior and generation is not None and prior["generation"] is not None:
                        if generation<prior["generation"] or (generation==prior["generation"] and intent!=prior["uuid"]):raise RelayError(409,"web_intent_replaced")
                        if intent==prior["uuid"] and generation!=prior["generation"]:raise RelayError(409,"web_intent_replaced")
                    session.intents[operation]={"uuid":intent,"generation":generation}
                headers["Idempotency-Key"]=self.sessions.upstream_key(token,operation,intent)
            if kind in ("native","progressive-source"):
                range_value=request.headers.get("range")
                if range_value and not re.fullmatch(r"bytes=(?:[0-9]{1,20}-[0-9]{0,20}|-[1-9][0-9]{0,19})",range_value):raise RelayError(416,"web_range_invalid")
                if range_value:headers["Range"]=range_value
                if value:=request.headers.get("if-range"):
                    if len(value)>256 or any(ord(c)<32 for c in value):raise RelayError(416,"web_range_invalid")
                    headers["If-Range"]=value
                job_path=path.removesuffix("/source") if kind=="progressive-source" else path.split("/annotated-video")[0]
                async with asyncio.timeout(max(.001,deadline-monotonic())):
                    check=await self.client.send(self.client.build_request("GET",self.settings.backend_url.rstrip("/")+job_path,headers={"X-API-Key":headers["X-API-Key"],"Accept-Encoding":"identity"}),stream=True)
                    try:
                        if check.status_code!=200:raise RelayError(check.status_code if check.status_code in (401,404,410) else 409,"web_media_unavailable")
                        metadata=await limited_json(check,deadline)
                    finally:await check.aclose()
                if (not metadata.get("media_available") if kind=="progressive-source" else metadata.get("status")!="completed"):raise RelayError(409,"web_media_unavailable")
                expiry=datetime.fromisoformat(metadata["expires_at"].replace("Z","+00:00"))
                deadline=min(deadline,monotonic()+(expiry-self.sessions.clock()).total_seconds())
            target=self.settings.backend_url.rstrip("/")+path
            if request.url.query:target+="?"+request.url.query
            async with asyncio.timeout(max(.001,deadline-monotonic())):
                response=await self.client.send(self.client.build_request(request.method,target,headers=headers,content=body),stream=True)
                if 300<=response.status_code<400:raise RelayError(502,"web_redirect_rejected")
                if response.headers.get("content-encoding","identity")!="identity":raise RelayError(502,"web_encoding_invalid")
                if response.status_code>=400:
                    code="web_upstream_failure"
                    if "application/json" in response.headers.get("content-type",""):
                        detail=await limited_json(response,deadline)
                        if isinstance(detail,dict) and re.fullmatch(r"[a-z0-9_]{1,64}",str(detail.get("code",""))):code=detail["code"]
                    return safe_error(response.status_code,code,{"Retry-After":"1"} if response.status_code==429 else {"Content-Range":response.headers["content-range"]} if response.status_code==416 and re.fullmatch(r"bytes \*/[0-9]{1,16}",response.headers.get("content-range","")) else None)
                if response.status_code==204:return Response(status_code=204,headers={"Cache-Control":"no-store"})
                if kind in ("json","enrich","image-upload","video-upload"):
                    payload=await limited_json(response,deadline)
                    if not self.sessions.get(token):raise RelayError(401,"web_session_expired")
                    return JSONResponse(payload,status_code=response.status_code,headers={"Cache-Control":"no-store"})
            maximum={"progressive-source":2*1024**3,"progressive-evidence":16*1024**2,"native":2*1024**3,"image":64*1024**2,"plate":2*1024**2}[kind]
            content_length=response.headers.get("content-length")
            content_range=response.headers.get("content-range","")
            total=re.search(r"/([0-9]+)$",content_range)
            if (content_length and (not content_length.isdigit() or int(content_length)>maximum)) or (total and int(total[1])>maximum):raise RelayError(502,"web_response_too_large")
            output_headers={"Cache-Control":"no-store","Cross-Origin-Resource-Policy":"same-origin"}
            for key in ("content-type","content-length","content-range","accept-ranges","etag","last-modified","x-plate-preview-metadata"):
                if value:=response.headers.get(key):
                    if key=="x-plate-preview-metadata" and (len(value)>2048 or not value.isascii()):raise RelayError(502,"web_metadata_invalid")
                    output_headers[key]=value
            upstream=response
            async def stream():
                size=0;iterator=upstream.aiter_bytes(65536).__aiter__()
                try:
                    while True:
                        if not self.sessions.get(token):raise RelayError(401,"web_session_expired")
                        left=deadline-monotonic()
                        if left<=0:raise RelayError(504,"web_timeout")
                        try:block=await asyncio.wait_for(anext(iterator),left)
                        except StopAsyncIteration:break
                        if not self.sessions.get(token) or monotonic()>=deadline:raise RelayError(401,"web_session_expired")
                        size+=len(block)
                        if size>maximum:raise RelayError(502,"web_response_too_large")
                        yield block
                finally:
                    await upstream.aclose();release()
            owned=False
            return StreamingResponse(stream(),status_code=response.status_code,headers=output_headers)
        except RelayError as exc:return safe_error(exc.status,exc.code)
        except (TimeoutError,httpx.TimeoutException):return safe_error(504,"web_timeout")
        except (httpx.HTTPError,ValueError,KeyError):return safe_error(502,"web_upstream_unavailable")
        finally:
            if owned:
                if response:await response.aclose()
                release()
