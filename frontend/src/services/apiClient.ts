import type { ApiError, Point } from "./apiTypes";

export class ClientError extends Error { constructor(public readonly status: number, public readonly detail: ApiError) { super(detail.message); } }
export class ApiClient {
  constructor(private readonly baseUrl: string, private readonly apiKey: string) {}
  private url(path: string) { return path.startsWith("http") ? path : `${this.baseUrl}${path}`; }
  private async request(path: string, init: RequestInit = {}) {
    const response = await fetch(this.url(path), { ...init, headers: { "X-API-Key": this.apiKey, ...(init.headers ?? {}) } });
    if (!response.ok) { let detail: ApiError = { code: "request_failed", message: "The request could not be completed." }; try { detail = await response.json(); } catch {} throw new ClientError(response.status, detail); }
    return response;
  }
  async json(path: string, init?: RequestInit) { return this.request(path, init).then(r => r.json()); }
  uploadImage(file: File) { const body = new FormData(); body.append("image", file); return this.json("/api/v1/detections/images", { method:"POST", body }); }
  uploadVideo(file: File) { const body = new FormData(); body.append("video", file); return this.json("/api/v1/video-jobs", { method:"POST", body }); }
  video(id:string) { return this.json(`/api/v1/video-jobs/${id}`); }
  cancelVideo(id:string) { return this.json(`/api/v1/video-jobs/${id}`, { method:"DELETE" }); }
  videoResults(id:string) { return Promise.all([this.json(`/api/v1/video-jobs/${id}/summary`), this.json(`/api/v1/video-jobs/${id}/detections?page=1&page_size=50`)]); }
  count(videoId:string, point_a:Point, point_b:Point) { return this.json(`/api/v1/video-jobs/${videoId}/count-jobs`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({point_a,point_b}) }); }
  countJob(id:string) { return this.json(`/api/v1/count-jobs/${id}`); }
  cancelCount(id:string) { return this.json(`/api/v1/count-jobs/${id}`, {method:"DELETE"}); }
  enrich(kind:"image"|"video", source_id:string) { return this.json("/api/v1/enrichment-jobs", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({source:{kind,source_id}})}); }
  enrichment(id:string) { return this.json(`/api/v1/enrichment-jobs/${id}`); }
  cancelEnrichment(id:string) { return this.json(`/api/v1/enrichment-jobs/${id}`, {method:"DELETE"}); }
  async blob(path:string) { return this.request(path).then(r => r.blob()); }
}
