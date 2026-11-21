import type { DetectionResponse } from "../../services/apiTypes";
import { classPresentation } from "./classPresentation";
export function DetectionContext({source,contextual,selected}:{source:DetectionResponse;contextual?:number;selected?:number}){
 const detection=source.detections.find(d=>d.detection_id===contextual);
 return <div className="detection-context">
  {detection?<><span className="context-id">#{detection.detection_id}</span><div><strong>{classPresentation(detection.class_name).label}</strong>
   <span>{contextual===selected?"Vehículo seleccionado":"En exploración · activa para abrir su ficha"}</span></div></>:<p>Selecciona un contorno o usa la lista para explorar cada vehículo.</p>}
  <span className="sr-only" role="status">{selected===undefined?"Sin vehículo seleccionado":"Vehículo seleccionado: "+selected}</span>
 </div>;
}
