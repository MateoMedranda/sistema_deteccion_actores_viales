export type Point = { x: number; y: number };
export type ApiError = { code: string; message: string; request_id?: string };
export type Box = {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
};
export type Detection = {
  detection_id: number;
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: Box;
  enrichment_eligible?: boolean;
};
export type ImageArtifact = {
  url: string;
  media_type: string;
  expires_at: string;
};
export type DetectionResponse = {
  request_id: string;
  status: "completed";
  processing_time_ms: number;
  image: { width: number; height: number; media_type: string };
  detections: Detection[];
  annotated_image: ImageArtifact;
  original_image?: ImageArtifact;
  source_expires_at?: string;
};
export type JobStatus =
  | "queued"
  | "processing"
  | "completed"
  | "failed"
  | "cancelled"
  | "expired";
export type Job = {
  job_id?: string;
  count_job_id?: string;
  enrichment_job_id?: string;
  status: string;
  progress_percent?: number;
  expires_at?: string;
  summary?: unknown[];
  events?: unknown[];
  error?: ApiError;
};
export type EnrichmentAccepted = {
  enrichment_job_id: string;
  status: JobStatus;
  created_at: string;
  expires_at: string;
};
export type EnrichmentJob = EnrichmentAccepted & {
  source: { kind: "image" | "video"; source_id: string };
  progress_percent: number;
  processed_units: number;
  total_units: number;
  results_ready: number;
};
export type PlateStatus = "read" | "unreadable" | "not_detected" | "failed";
export type VehicleResult = {
  vehicle_key: string;
  detection_id: number;
  track_id: number | null;
  class_id: number;
  class_name: string;
  attributes_status: "completed" | "failed";
  attributes: { name: string; label: string; confidence: number }[];
  plate_status: PlateStatus;
  plate: {
    status: PlateStatus;
    text: string | null;
    bbox_relative?: Box;
    localizer_confidence?: number;
    ocr_confidence?: number;
    used_enhancement: boolean;
    provenance?:PlateProvenance;
  };
  error_code?: string;
};
export type EnrichmentPage = {
  items: VehicleResult[];
  page: number;
  page_size: number;
  total: number;
};


export type PlateProvenance={version:1;policy_id:"baseline-v1"|"candidate-rescue-v1"|"legacy-unknown";attempted_variants:string[];selected_variant:string};
export function parsePlateProvenance(value:unknown,status:PlateStatus):PlateProvenance|undefined{
 if(value==null)return;
 const p=obj(value),policy=text(p.policy_id),selected=text(p.selected_variant);
 const variants=["raw","legacy-retry-v1","bilateral-clahe-v1","bilateral-adaptive-v1"],attempts=array(p.attempted_variants).map(text);
 if(Object.keys(p).length!==4||p.version!==1||!["baseline-v1","candidate-rescue-v1","legacy-unknown"].includes(policy)||attempts.some(v=>!variants.includes(v))||new Set(attempts).size!==attempts.length)throw new Error("invalid_provenance");
 if(policy==="legacy-unknown"){if(attempts.length||!["unknown","none"].includes(selected))throw new Error("invalid_provenance");}
 else if(status==="read"?!attempts.includes(selected):selected!=="none")throw new Error("invalid_provenance");
 if(policy==="baseline-v1"&&attempts.some(v=>!["raw","legacy-retry-v1"].includes(v)))throw new Error("invalid_provenance");
 return {version:1,policy_id:policy as PlateProvenance["policy_id"],attempted_variants:attempts,selected_variant:selected};
}

export type PlatePreviewContext={sourceId:string;jobId:string;detectionId:number;box:Box;expiresAt:number};
export type PlatePreviewMetadata={
 version:1;source_id:string;enrichment_job_id:string;detection_id:number;profile_id:"display-contrast-v1";
 input_size:{width:number;height:number};output_size:{width:number;height:number};original_bbox:Box;
 applied_steps:string[];original_to_processed:number[];expires_at:string;
};
export function parsePlatePreviewMetadata(value:unknown,expected:PlatePreviewContext):PlatePreviewMetadata{
 const m=obj(value);
 const keys=["version","source_id","enrichment_job_id","detection_id","profile_id","input_size","output_size","original_bbox","applied_steps","original_to_processed","expires_at"];
 if(Object.keys(m).length!==keys.length||keys.some(k=>!Object.prototype.hasOwnProperty.call(m,k)))throw new Error("invalid_preview");
 const sid=text(m.source_id),jid=text(m.enrichment_job_id),id=integer(m.detection_id,1);
 if(m.version!==1||m.profile_id!=="display-contrast-v1"||sid.length>128||jid.length>128||sid!==expected.sourceId||jid!==expected.jobId||id!==expected.detectionId)throw new Error("invalid_preview");
 const size=(v:unknown,max:number)=>{const s=obj(v);if(Object.keys(s).sort().join(",")!=="height,width")throw new Error("invalid_size");return {width:integer(s.width,2),height:integer(s.height,2)};};
 const input=size(m.input_size,Infinity),output=size(m.output_size,2048);
 if(output.width>2048||output.height>2048||output.width*output.height>2_000_000)throw new Error("invalid_size");
 const roi=box(m.original_bbox);
 if(Object.keys(obj(m.original_bbox)).length!==4||Object.keys(roi).some(k=>roi[k as keyof Box]!==expected.box[k as keyof Box]))throw new Error("invalid_roi");
 const matrix=array(m.original_to_processed).map(v=>num(v)),scale=matrix[0];
 if(matrix.length!==6||![1,2,3,4].includes(scale)||matrix.some((v,i)=>v!==[scale,0,0,0,scale,0][i]))throw new Error("invalid_matrix");
 if(input.width!==roi.x_max-roi.x_min||input.height!==roi.y_max-roi.y_min||output.width!==input.width*scale||output.height!==input.height*scale)throw new Error("invalid_size");
 const steps=array(m.applied_steps).map(text),wanted=["grayscale",...(scale>1?["resize_integer"]:[]),"clahe"];
 if(steps.join(",")!==wanted.join(","))throw new Error("invalid_steps");
 const expires=date(m.expires_at),expiry=Date.parse(expires);
 if(!/(Z|\+00:00)$/.test(expires)||expiry<=Date.now()||expiry>expected.expiresAt)throw new Error("invalid_expiry");
 return {version:1,source_id:sid,enrichment_job_id:jid,detection_id:id,profile_id:"display-contrast-v1",input_size:input,output_size:output,original_bbox:roi,applied_steps:steps,original_to_processed:matrix,expires_at:expires};
}

export const terminal = new Set([
  "completed",
  "failed",
  "cancelled",
  "expired",
]);

function obj(v: unknown): Record<string, unknown> {
  if (!v || typeof v !== "object" || Array.isArray(v))
    throw new Error("invalid_response");
  return v as Record<string, unknown>;
}
function text(v: unknown): string {
  if (typeof v !== "string" || !v.trim()) throw new Error("invalid_response");
  return v;
}
function num(v: unknown, minimum = 0, maximum = Infinity): number {
  if (
    typeof v !== "number" ||
    !Number.isFinite(v) ||
    v < minimum ||
    v > maximum
  )
    throw new Error("invalid_response");
  return v;
}
function integer(v: unknown, minimum = 0): number {
  const n = num(v, minimum);
  if (!Number.isInteger(n)) throw new Error("invalid_response");
  return n;
}
function date(v: unknown): string {
  const s = text(v);
  if (!Number.isFinite(Date.parse(s))) throw new Error("invalid_response");
  return s;
}
function array(v: unknown): unknown[] {
  if (!Array.isArray(v)) throw new Error("invalid_response");
  return v;
}
function box(
  v: unknown,
  width = Infinity,
  height = Infinity,
  relative = false,
): Box {
  const b = obj(v);
  const parse = relative
    ? (v: unknown) => num(v, 0, 1)
    : (v: unknown) => integer(v);
  const result = {
    x_min: parse(b.x_min),
    y_min: parse(b.y_min),
    x_max: parse(b.x_max),
    y_max: parse(b.y_max),
  };
  if (
    result.x_max <= result.x_min ||
    result.y_max <= result.y_min ||
    result.x_max > width ||
    result.y_max > height
  )
    throw new Error("invalid_response");
  return result;
}
function artifact(v: unknown): ImageArtifact {
  const a = obj(v),
    mime = text(a.media_type);
  if (!["image/png", "image/jpeg"].includes(mime))
    throw new Error("invalid_response");
  return { url: text(a.url), media_type: mime, expires_at: date(a.expires_at) };
}
function status(v: unknown): JobStatus {
  if (
    typeof v !== "string" ||
    ![
      "queued",
      "processing",
      "completed",
      "failed",
      "cancelled",
      "expired",
    ].includes(v)
  )
    throw new Error("invalid_response");
  return v as JobStatus;
}
export function parseDetectionResponse(value: unknown): DetectionResponse {
  const r = obj(value),
    image = obj(r.image),
    width = integer(image.width, 1),
    height = integer(image.height, 1);
  if (
    r.status !== "completed" ||
    !["image/jpeg", "image/png"].includes(text(image.media_type))
  )
    throw new Error("invalid_response");
  const seen = new Set<number>();
  const detections = array(r.detections).map((value) => {
    const d = obj(value),
      id = integer(d.detection_id, 1);
    if (
      seen.has(id) ||
      (d.enrichment_eligible !== undefined &&
        typeof d.enrichment_eligible !== "boolean")
    )
      throw new Error("invalid_response");
    seen.add(id);
    return {
      detection_id: id,
      class_id: integer(d.class_id),
      class_name: text(d.class_name),
      confidence: num(d.confidence, 0, 1),
      bbox: box(d.bbox, width, height),
      enrichment_eligible: d.enrichment_eligible as boolean | undefined,
    };
  });
  const original =
    r.original_image == null ? undefined : artifact(r.original_image);
  if (original && original.media_type !== "image/png")
    throw new Error("invalid_response");
  return {
    request_id: text(r.request_id),
    status: "completed",
    processing_time_ms: num(r.processing_time_ms),
    image: { width, height, media_type: text(image.media_type) },
    detections,
    annotated_image: artifact(r.annotated_image),
    original_image: original,
    source_expires_at:
      r.source_expires_at == null ? undefined : date(r.source_expires_at),
  };
}
export function parseEnrichmentAccepted(value: unknown): EnrichmentAccepted {
  const r = obj(value);
  return {
    enrichment_job_id: text(r.enrichment_job_id),
    status: status(r.status),
    created_at: date(r.created_at),
    expires_at: date(r.expires_at),
  };
}
export function parseEnrichmentJob(value: unknown): EnrichmentJob {
  const r = obj(value),
    source = obj(r.source),
    total = integer(r.total_units),
    processed = integer(r.processed_units);
  if (!["image", "video"].includes(text(source.kind)) || processed > total)
    throw new Error("invalid_response");
  return {
    ...parseEnrichmentAccepted(r),
    source: {
      kind: source.kind as "image" | "video",
      source_id: text(source.source_id),
    },
    processed_units: processed,
    total_units: total,
    results_ready: integer(r.results_ready),
    progress_percent: num(r.progress_percent, 0, 100),
  };
}
export function parseEnrichmentPage(value: unknown): EnrichmentPage {
  const r = obj(value),
    page = integer(r.page, 1),
    size = integer(r.page_size, 1),
    total = integer(r.total);
  if (size > 100) throw new Error("invalid_response");
  const seen = new Set<number>();
  const items = array(r.items).map((value) => {
    const v = obj(value),
      p = obj(v.plate),
      id = integer(v.detection_id, 1),
      state = text(p.status);
    if (
      seen.has(id) ||
      !["read", "unreadable", "not_detected", "failed"].includes(state) ||
      v.plate_status !== state ||
      !["completed", "failed"].includes(text(v.attributes_status))
    )
      throw new Error("invalid_response");
    seen.add(id);
    const plateText = state === "read" ? text(p.text) : null;
    return {
      vehicle_key: text(v.vehicle_key),
      detection_id: id,
      track_id: v.track_id == null ? null : integer(v.track_id, 1),
      class_id: integer(v.class_id),
      class_name: text(v.class_name),
      attributes_status: v.attributes_status as "completed" | "failed",
      attributes: array(v.attributes).map((value) => {
        const a = obj(value);
        return {
          name: text(a.name),
          label: text(a.label),
          confidence: num(a.confidence, 0, 1),
        };
      }),
      plate_status: state as PlateStatus,
      plate: {
        status: state as PlateStatus,
        text: plateText,
        bbox_relative:
          p.bbox_relative == null || state === "not_detected"
            ? undefined
            : box(p.bbox_relative, 1, 1, true),
        localizer_confidence:
          p.localizer_confidence == null
            ? undefined
            : num(p.localizer_confidence, 0, 1),
        ocr_confidence:
          p.ocr_confidence == null ? undefined : num(p.ocr_confidence, 0, 1),
        used_enhancement: p.used_enhancement === true,
        provenance:parsePlateProvenance(p.provenance,state as PlateStatus),
      },
      error_code:
        typeof v.error_code === "string" &&
        /^[a-z0-9_]{1,64}$/.test(v.error_code)
          ? v.error_code
          : undefined,
    };
  });
  if (items.length > size || items.length > total)
    throw new Error("invalid_response");
  return { items, page, page_size: size, total };
}

export type ImagePolicy = {
  media_types: string[];
  max_upload_bytes: number;
  max_image_pixels: number;
};
export function parseImagePolicy(value: unknown): ImagePolicy {
  const r = obj(value),
    media = array(r.media_types).map(text);
  if (
    !media.length ||
    media.some((m) => !["image/jpeg", "image/png"].includes(m))
  )
    throw new Error("invalid_policy");
  return {
    media_types: media,
    max_upload_bytes: integer(r.max_upload_bytes, 1),
    max_image_pixels: integer(r.max_image_pixels, 1),
  };
}

export {parseWebSession} from "./managedTypes";
export type {WebSessionReady,WebPolicy} from "./managedTypes";

export {parseVideoJob} from "../features/video-analysis/videoTypes";
export type {VideoJob,VideoMetadata} from "../features/video-analysis/videoTypes";
