export type Point = { x: number; y: number };
export type ApiError = { code: string; message: string; request_id?: string };
export type Detection = { class_name: string; confidence: number; x_min: number; y_min: number; x_max: number; y_max: number };
export type Job = { job_id?: string; count_job_id?: string; enrichment_job_id?: string; status: string; progress_percent?: number; expires_at?: string; summary?: unknown[]; events?: unknown[]; error?: ApiError };
export const terminal = new Set(["completed", "failed", "cancelled", "expired"]);

