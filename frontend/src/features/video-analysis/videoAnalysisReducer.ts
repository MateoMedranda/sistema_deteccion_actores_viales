import type {VideoJob} from "./videoTypes";
import type {EnrichmentJob} from "../../services/apiTypes";
export type ProcessingState="idle"|"uploading"|"checking"|"queued"|"processing"|"ready"|"failed"|"cancelled"|"interrupted"|"expired";
export type EnrichmentState="waiting"|"submitting"|"queued"|"processing"|"completed"|"not_applicable"|"failed"|"cancelled"|"interrupted"|"expired";
export type MediaState="idle"|"loading"|"available"|"failed"|"expired";
export type VideoAnalysisState={generation:number;file?:File;video?:VideoJob;enriched?:EnrichmentJob;processing:ProcessingState;enrichment:EnrichmentState;media:MediaState;message:string};
export const initialVideoState:VideoAnalysisState={generation:0,processing:"idle",enrichment:"waiting",media:"idle",message:"Selecciona un video para comenzar."};
export type VideoAction={generation:number}&(
 {type:"reset";file?:File}|{type:"processing";value:ProcessingState}|{type:"enrichment";value:EnrichmentState}|{type:"media";value:MediaState}|
 {type:"message";value:string}|{type:"video";value:VideoJob}|{type:"enriched";value:EnrichmentJob}|{type:"retire";scope:"source"|"enrichment"});
export function videoAnalysisReducer(state:VideoAnalysisState,action:VideoAction):VideoAnalysisState{
 if(action.type==="reset")return action.generation>state.generation?{...initialVideoState,generation:action.generation,file:action.file}:state;
 if(action.generation!==state.generation)return state;
 switch(action.type){
 case "processing":return {...state,processing:action.value};
 case "enrichment":return {...state,enrichment:action.value};
 case "media":return {...state,media:action.value};
 case "message":return {...state,message:action.value};
 case "video":return {...state,video:action.value};
 case "enriched":return {...state,enriched:action.value};
 case "retire":return action.scope==="source"?{...initialVideoState,generation:state.generation,processing:"expired",media:"expired",enrichment:"expired",message:"El video ha vencido. Selecciona una fuente nueva."}:{...state,enriched:undefined,enrichment:"expired",message:"El enriquecimiento ha vencido; el video continúa disponible mientras siga vigente."};
 }
}
