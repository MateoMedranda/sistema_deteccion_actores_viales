import type { CSSProperties } from "react";
import {SceneViewport} from "./SceneViewport";
import type { DetectionResponse } from "../../services/apiTypes";
import { projectBox } from "../../utils/imageGeometry";
import { classPresentation } from "./classPresentation";
export type ContextEvent = "hover"|"leave"|"focus"|"blur";
export type ContextHandler = (event:ContextEvent,id:number,sourceId:string)=>void;
export function AnnotatedImageViewer({source,url,selected,contextual,onSelect,onContext,state="loading",onRetry,onFailure}:{
 source:DetectionResponse;url:string;selected?:number;onSelect:(id:number)=>void;
 contextual?:{id:number;state:"focus"|"hover"|"selected"};
 onContext?:ContextHandler;state?:"idle"|"loading"|"ready"|"failed";onRetry?:()=>void;onFailure?:()=>void;
}){
 return <div className="scene-frame">{url?<SceneViewport sourceId={source.request_id} width={source.image.width} height={source.image.height}>
  <img src={url} onError={onFailure} alt="Escena vial original con contornos de detección"/>
  {source.detections.map(d=>{
   const geometry=projectBox(d.bbox,source.image.width,source.image.height);
   if(!geometry)return null;
   const p=classPresentation(d.class_name),style={...geometry,"--class-color":p.color} as CSSProperties;
   if(d.enrichment_eligible!==true)return <div key={d.detection_id} className="scene-contour noninteractive" style={style} aria-hidden="true" data-class={p.key}/>;
   const context=(e:ContextEvent)=>onContext?.(e,d.detection_id,source.request_id);
   return <button key={d.detection_id} className="scene-contour" style={style} data-class={p.key}
    aria-label={"Detección "+d.detection_id+", "+p.label} aria-pressed={selected===d.detection_id}
    data-context={contextual?.id===d.detection_id?contextual.state:undefined}
    aria-controls="vehicle-details" onClick={()=>onSelect(d.detection_id)}
    onPointerEnter={()=>context("hover")} onPointerLeave={()=>context("leave")}
    onFocus={()=>context("focus")} onBlur={()=>context("blur")}/>;
  })}
 </SceneViewport>:<div className="scene-placeholder"><div><p>{state==="failed"||state==="idle"?"La escena original no está disponible.":"Cargando escena original…"}</p>
 {state==="failed"&&<button onClick={onRetry}>Reintentar original</button>}</div></div>}</div>;
}
