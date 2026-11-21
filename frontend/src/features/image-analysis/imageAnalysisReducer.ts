import type { EnrichmentStage } from "./types";
import type { DetectionResponse, VehicleResult } from "../../services/apiTypes";
export type Phase =
  | "idle"
  | "ready"
  | "detecting"
  | "enriching"
  | "completed"
  | "partial"
  | "empty"
  | "failed"
  | "interrupted"
  | "expired"
  | "cancelled";
export type ImageState = {
  phase: Phase;
  file?: File;
  preview: string;
  response?: DetectionResponse;
  annotated: string;
  annotatedState: "idle" | "loading" | "ready" | "failed";
  originalState: "idle" | "loading" | "ready" | "failed";
  original: string;
  results: Record<number, VehicleResult>;
  selected?: number;
  focusedDetectionId?: number;
  hoveredDetectionId?: number;
  progress: number;
  message: string;
  warning: string;
  jobId?: string;
  generation: number;
  expiresAt?: number;
  enrichmentStage?: EnrichmentStage;
};
export const initialState: ImageState = {
  phase: "idle",
  file: undefined,
  response: undefined,
  selected: undefined,
  jobId: undefined,
  expiresAt: undefined,
  enrichmentStage: undefined,
  preview: "",
  annotated: "",
  annotatedState: "idle",
  originalState: "idle",
  original: "",
  results: {},
  progress: 0,
  message: "",
  warning: "",
  generation: 0,
};
export function imageAnalysisReducer(
  state: ImageState,
  patch: Partial<ImageState> | {contextEvent:"hover"|"leave"|"focus"|"blur";detectionId:number;sourceId:string;generation:number},
): ImageState {
  if ("contextEvent" in patch) return patch.generation===state.generation?sceneInteraction(state,patch.contextEvent,patch.detectionId,patch.sourceId):state;
  const next={ ...state, ...patch };
  if (next.generation!==state.generation || next.response?.request_id!==state.response?.request_id) {
    next.focusedDetectionId=undefined; next.hoveredDetectionId=undefined;
  }
  return next;
}

export function contextualDetectionId(state:ImageState){
 const valid=(id?:number)=>state.response?.detections.some(d=>d.detection_id===id&&d.enrichment_eligible===true)?id:undefined;
 return valid(state.focusedDetectionId)??valid(state.hoveredDetectionId)??valid(state.selected);
}
export function sceneInteraction(state:ImageState,event:"hover"|"leave"|"focus"|"blur",id:number,sourceId:string):ImageState{
 if(state.response?.request_id!==sourceId||!state.response.detections.some(d=>d.detection_id===id&&d.enrichment_eligible===true))return state;
 const key=event==="focus"||event==="blur"?"focusedDetectionId":"hoveredDetectionId";
 if((event==="leave"||event==="blur")&&state[key]!==id)return state;
 return {...state,[key]:event==="leave"||event==="blur"?undefined:id};
}
