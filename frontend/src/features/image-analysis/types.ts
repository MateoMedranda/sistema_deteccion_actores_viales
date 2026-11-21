export type { ImageState, Phase } from "./imageAnalysisReducer";
export type {
  Detection,
  DetectionResponse,
  VehicleResult,
  PlateStatus,
} from "../../services/apiTypes";
export type EnrichmentStage =
  | "idle"
  | "submitting"
  | "queued"
  | "processing"
  | "completed"
  | "failed"
  | "cancelled";
