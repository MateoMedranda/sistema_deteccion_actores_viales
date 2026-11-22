import type {WebPolicy} from "./managedTypes";
import { parseImagePolicy, parsePlatePreviewMetadata, type PlatePreviewContext } from "./apiTypes";
import { decodeImage } from "../utils/decodeImage";
import type {
  ApiError,
  Point,
  DetectionResponse,
  EnrichmentAccepted,
  EnrichmentJob,
  EnrichmentPage,
} from "./apiTypes";
import {
  parseDetectionResponse,
  parseEnrichmentAccepted,
  parseEnrichmentJob,
  parseEnrichmentPage,
} from "./apiTypes";

export type RequestOptions = {
  signal?: AbortSignal;
  intent?: string;
  intentGeneration?: number;
  timeoutMs?: number;
  deadline?: number;
  expiresAt?: string | number;
};
export class ClientError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: ApiError,
  ) {
    super(detail.message);
    this.name = "ClientError";
  }
}
const error = (code: string, status = 0) =>
  new ClientError(status, {
    code,
    message: "No se pudo completar la solicitud.",
  });
const read = <T>(value: unknown, parse: (value: unknown) => T): T => {
  try {
    return parse(value);
  } catch {
    throw error("invalid_response");
  }
};
export const imageTimeouts = {
  detection: 120_000,
  creation: 15_000,
  status: 10_000,
  evidence: 30_000,
  cycle: 120_000,
};

export class ApiClient {
  private readonly baseUrl: string;
  private readonly origin: string;
  private controllers=new Set<AbortController>();
  private accepted=new Map<string,string>();
  private intentSequence=0;
  newVideoIntent(){return {intent:crypto.randomUUID(),intentGeneration:++this.intentSequence};}
  get policy(){return this.web?.policy;}
  get managed(){return !!this.web;}
  get csrfToken(){return this.web?.csrf;}
  async shutdown(){
    for(const c of this.controllers)c.abort();
    await Promise.allSettled([...this.accepted.values()].map(path=>this.json(path,{method:"DELETE"},{timeoutMs:5000})));
    this.accepted.clear();
  }
  nativeVideo(id:string,count=false){
    if(!this.web)throw error("managed_transport_required");
    return this.url(count?"/api/v1/count-jobs/"+encodeURIComponent(id)+"/annotated-video":"/api/v1/video-jobs/"+encodeURIComponent(id)+"/annotated-video/content");
  }
  constructor(
    baseUrl: string,
    private readonly apiKey: string,
    private readonly web?: {csrf:string;expiresAt:number;onRejected?:()=>void;policy?:WebPolicy},
  ) {
    const base = new URL(baseUrl);
    if (
      !["http:", "https:"].includes(base.protocol) ||
      base.username ||
      base.password
    )
      throw error("invalid_service_url");
    this.origin = base.origin;
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  private url(path: string) {
    let target: URL;
    try {
      target = new URL(
        path.startsWith("/") ? this.baseUrl + path : path,
        this.baseUrl + "/",
      );
    } catch {
      throw error("unsafe_artifact_url");
    }
    if (target.origin !== this.origin || target.username || target.password)
      throw error("unsafe_artifact_url");
    if(this.web&&!target.pathname.startsWith(new URL(this.baseUrl).pathname+"/"))throw error("unsafe_artifact_url");
    return target.href;
  }

  private async consume<T>(
    path: string,
    body: (response: Response, signal:AbortSignal, restrictExpiry:(expiresAt:number)=>void) => Promise<T>,
    init: RequestInit = {},
    options: RequestOptions = {},
  ): Promise<T> {
    if(this.web)options={...options,expiresAt:Math.min(this.web.expiresAt,typeof options.expiresAt==="number"?options.expiresAt:options.expiresAt?Date.parse(options.expiresAt):Infinity)};
    const url = this.url(path);
    let remaining = options.timeoutMs ?? Infinity;
    if (options.deadline !== undefined)
      remaining = Math.min(remaining, options.deadline - performance.now());
    if (options.expiresAt !== undefined) {
      const expiry =
        typeof options.expiresAt === "number"
          ? options.expiresAt
          : Date.parse(options.expiresAt);
      remaining = Math.min(remaining, expiry - Date.now());
    }
    if (remaining <= 0 || Number.isNaN(remaining))
      throw error("request_timeout");
    const controller = new AbortController();
    let timedOut = false,
      received = false,
      evidenceExpired = false;
    const operationEnd=performance.now()+remaining;
    const abort = () => controller.abort();
    if (options.signal?.aborted)
      throw new DOMException("Aborted", "AbortError");
    this.controllers.add(controller);
    options.signal?.addEventListener("abort", abort, { once: true });
    let timer = Number.isFinite(remaining)
      ? setTimeout(() => {
          timedOut = true;
          controller.abort();
        }, remaining)
      : undefined;
    const restrictExpiry=(expiresAt:number)=>{
      const ttl=expiresAt-Date.now(),budget=operationEnd-performance.now();
      if(timer!==undefined)clearTimeout(timer);
      const expiryFirst=ttl<=budget;
      timer=setTimeout(()=>{evidenceExpired=expiryFirst;timedOut=true;controller.abort();},Math.max(0,Math.min(ttl,budget)));
    };
    try {
      const response = await fetch(url, {
        ...init,
        redirect: "error",
        signal: controller.signal,
        credentials:this.web?"same-origin":"omit",
        headers: { ...init.headers, ...(this.web?{"X-UI-Request":"1","X-UI-CSRF":this.web.csrf}:{"X-API-Key":this.apiKey}),...(options.intent?{"X-UI-Intent":options.intent}:{}),...(options.intentGeneration?{"X-UI-Intent-Generation":String(options.intentGeneration)}:{}) },
      });
      received = true;
      if(this.web&&[401,403].includes(response.status))this.web.onRejected?.();
      if (!response.ok) {
        if ([401, 404, 410].includes(response.status)) {
          controller.abort();
          throw error("access_unavailable", response.status);
        }
        let code = "request_failed";
        try {
          const detail: unknown = await response.json();
          if (
            detail &&
            typeof detail === "object" &&
            "code" in detail &&
            typeof detail.code === "string" &&
            /^[a-z0-9_]{1,64}$/.test(detail.code)
          )
            code = detail.code;
        } catch {
          /* Response bodies are never shown directly. */
        }
        throw error(code, response.status);
      }
      // The deadline stays active while JSON or image bytes are being consumed.
      return await body(response,controller.signal,restrictExpiry);
    } catch (cause) {
      controller.abort();
      if (evidenceExpired) throw error("access_unavailable",410);
      if (timedOut) throw error("request_timeout");
      if (options.signal?.aborted)
        throw new DOMException("Aborted", "AbortError");
      if (cause instanceof ClientError) throw cause;
      throw error(received ? "invalid_response" : "network_unavailable");
    } finally {
      this.controllers.delete(controller);
      if (timer !== undefined) clearTimeout(timer);
      options.signal?.removeEventListener("abort", abort);
    }
  }

  async json<T = unknown>(
    path: string,
    init?: RequestInit,
    options?: RequestOptions,
  ): Promise<T> {
    const result=await this.consume<T>(path,(response)=>response.json() as Promise<T>,init,options);
    if(this.web&&init?.method==="POST"&&result&&typeof result==="object"){
      const value=result as Record<string,unknown>;
      const entry=typeof value.job_id==="string"?["video","/api/v1/video-jobs/"+value.job_id]:typeof value.count_job_id==="string"?["count","/api/v1/count-jobs/"+value.count_job_id]:typeof value.enrichment_job_id==="string"?["enrichment","/api/v1/enrichment-jobs/"+value.enrichment_job_id]:undefined;
      if(entry){let kind=entry[0];if(kind==="enrichment"&&typeof init.body==="string"){try{kind+=":"+JSON.parse(init.body).source.kind;}catch{}}this.accepted.set(kind,entry[1]);}
    }
    if(init?.method==="DELETE")for(const [key,value] of this.accepted)if(value===path)this.accepted.delete(key);
    return result;
  }

  blob(path: string, options?: RequestOptions) {
    return this.consume(path, (response) => response.blob(), {}, options);
  }


  async platePreview(context:PlatePreviewContext,options:RequestOptions={}){
    const deadline=Math.min(options.deadline??Infinity,performance.now()+10_000);
    return this.consume("/api/v1/enrichment-jobs/"+encodeURIComponent(context.jobId)+"/detections/"+context.detectionId+"/plate-preview?profile=display-contrast-v1",async(response,signal,restrictExpiry)=>{
      const header=response.headers.get("X-Plate-Preview-Metadata");
      if(!header||header.length>2048||/[^\x20-\x7e]/.test(header)||response.headers.get("Content-Type")?.split(";")[0].trim()!=="image/png")throw error("invalid_response");
      const metadata=read(JSON.parse(header),(v)=>parsePlatePreviewMetadata(v,context));
      restrictExpiry(Date.parse(metadata.expires_at));
      const reader=response.body?.getReader();
      if(!reader)throw error("invalid_response");
      const chunks:Uint8Array[]=[];let length=0;
      const abort=()=>{void reader.cancel().catch(()=>{});};
      signal.addEventListener("abort",abort,{once:true});
      try{
        while(true){
          const {value,done}=await reader.read();
          if(signal.aborted)throw new DOMException("Aborted","AbortError");
          if(done)break;
          length+=value.byteLength;
          if(length>2*1024*1024)throw error("invalid_response");
          chunks.push(value);
        }
      }finally{signal.removeEventListener("abort",abort);void reader.cancel().catch(()=>{});}
      const bytes=new Uint8Array(length);let offset=0;
      for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}
      if(![137,80,78,71,13,10,26,10].every((b,i)=>bytes[i]===b))throw error("invalid_response");
      const blob=new Blob([bytes],{type:"image/png"}),url=URL.createObjectURL(blob);
      try{
        const size=await decodeImage(url,signal,Math.min(deadline-performance.now(),Date.parse(metadata.expires_at)-Date.now()));
        if(size.width!==metadata.output_size.width||size.height!==metadata.output_size.height||signal.aborted||performance.now()>=deadline||Date.now()>=Date.parse(metadata.expires_at))throw error("invalid_response");
        return {blob,metadata};
      }finally{URL.revokeObjectURL(url);}
    },{},{...options,deadline,expiresAt:Math.min(context.expiresAt,typeof options.expiresAt==="number"?options.expiresAt:options.expiresAt?Date.parse(options.expiresAt):Infinity),timeoutMs:Math.min(options.timeoutMs??10000,10000)});
  }

  async imagePolicy(options: RequestOptions = {}) {
    return read(
      await this.json("/health/image-policy", undefined, {
        timeoutMs: imageTimeouts.status,
        ...options,
      }),
      parseImagePolicy,
    );
  }

  async uploadImage(
    file: File,
    options: RequestOptions = {},
  ): Promise<DetectionResponse> {
    const body = new FormData();
    body.append("image", file);
    return read(
      await this.json(
        "/api/v1/detections/images",
        { method: "POST", body },
        { timeoutMs: imageTimeouts.detection, ...options },
      ),
      parseDetectionResponse,
    );
  }
  annotatedImage(id: string, options: RequestOptions = {}) {
    return this.blob(
      "/api/v1/detections/" + encodeURIComponent(id) + "/annotated-image",
      { timeoutMs: imageTimeouts.evidence, ...options },
    );
  }
  originalImage(path: string, options: RequestOptions = {}) {
    return this.blob(path, { timeoutMs: imageTimeouts.evidence, ...options });
  }
  async enrich(
    kind: "image" | "video",
    sourceId: string,
    options?: RequestOptions,
  ): Promise<EnrichmentAccepted> {
    const value = await this.json(
      "/api/v1/enrichment-jobs",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: { kind, source_id: sourceId } }),
      },
      kind === "image"
        ? { timeoutMs: imageTimeouts.creation, ...options }
        : options,
    );
    return read(value, parseEnrichmentAccepted);
  }
  async enrichment(
    id: string,
    options?: RequestOptions,
  ): Promise<EnrichmentJob> {
    return read(
      await this.json(
        "/api/v1/enrichment-jobs/" + encodeURIComponent(id),
        undefined,
        options,
      ),
      parseEnrichmentJob,
    );
  }
  async enrichmentResults(
    id: string,
    page = 1,
    pageSize = 50,
    options?: RequestOptions,
  ): Promise<EnrichmentPage> {
    return read(
      await this.json(
        "/api/v1/enrichment-jobs/" +
          encodeURIComponent(id) +
          "/results?page=" +
          page +
          "&page_size=" +
          pageSize,
        undefined,
        options,
      ),
      parseEnrichmentPage,
    );
  }
  cancelEnrichment(id: string, options?: RequestOptions) {
    return this.json(
      "/api/v1/enrichment-jobs/" + encodeURIComponent(id),
      { method: "DELETE" },
      options,
    );
  }

  // Existing video/count callers retain their signatures and have no image timeout defaults.
  uploadVideo(file: File, options?: RequestOptions) {
    const body = new FormData();
    body.append("video", file);
    return this.json<any>(
      "/api/v1/video-jobs",
      { method: "POST", body },
      options,
    );
  }
  video(id: string, options?: RequestOptions) {
    return this.json<any>(
      "/api/v1/video-jobs/" + encodeURIComponent(id),
      undefined,
      options,
    );
  }
  cancelVideo(id: string) {
    return this.json<any>(
      "/api/v1/video-jobs/" + encodeURIComponent(id),
      { method: "DELETE" },
      { timeoutMs: 5_000 },
    );
  }
  videoResults(id: string) {
    return Promise.all([
      this.json<any>("/api/v1/video-jobs/" + id + "/summary"),
      this.json<any>(
        "/api/v1/video-jobs/" + id + "/detections?page=1&page_size=50",
      ),
    ]);
  }
  annotatedVideo(id: string, options?: RequestOptions) {
    return this.json<{ url: string }>(
      "/api/v1/video-jobs/" + id + "/annotated-video",
      undefined,
      options,
    ).then((item) => this.blob(item.url, options));
  }
  count(
    videoId: string,
    point_a: Point,
    point_b: Point,
    options?: RequestOptions,
  ) {
    return this.json<any>(
      "/api/v1/video-jobs/" + videoId + "/count-jobs",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ point_a, point_b }),
      },
      options,
    );
  }
  countJob(id: string, options?: RequestOptions) {
    return this.json<any>("/api/v1/count-jobs/" + id, undefined, options);
  }
  cancelCount(id: string) {
    return this.json<any>(
      "/api/v1/count-jobs/" + id,
      { method: "DELETE" },
      { timeoutMs: 5_000 },
    );
  }
}
