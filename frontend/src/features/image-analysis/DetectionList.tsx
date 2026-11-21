import type { CSSProperties } from "react";
import type { DetectionResponse } from "../../services/apiTypes";
import { classPresentation } from "./classPresentation";
import type { ContextHandler,ContextEvent } from "./AnnotatedImageViewer";
export function DetectionList({source,selected,onSelect,onContext}:{source:DetectionResponse;selected?:number;onSelect:(id:number)=>void;onContext?:ContextHandler}){
 return <div className="detection-list" aria-label="Vehículos detectados">{source.detections.filter(d=>d.enrichment_eligible===true).map(d=>{
 const p=classPresentation(d.class_name),context=(e:ContextEvent)=>onContext?.(e,d.detection_id,source.request_id);
 return <button key={d.detection_id} className={"detection-chip "+(selected===d.detection_id?"selected":"")} style={{"--class-color":p.color} as CSSProperties}
 aria-pressed={selected===d.detection_id} aria-controls="vehicle-details" onClick={()=>onSelect(d.detection_id)}
 onPointerEnter={()=>context("hover")} onPointerLeave={()=>context("leave")} onFocus={()=>context("focus")} onBlur={()=>context("blur")}>
 <span className="chip-id">#{d.detection_id}</span><span>Detección {d.detection_id}<small>{p.label}</small></span><span aria-hidden="true">↗</span></button>;
 })}</div>;
}
