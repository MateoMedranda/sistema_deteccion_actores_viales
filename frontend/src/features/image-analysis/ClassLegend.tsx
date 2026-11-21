import type { DetectionResponse } from "../../services/apiTypes";
import {classPresentation} from "./classPresentation";
export function ClassLegend({source}:{source:DetectionResponse}){
 const classes=[...new Map(source.detections.map(d=>{const p=classPresentation(d.class_name);return [p.key,p] as const;})).values()];
 return <div className="class-legend" aria-label="Clases presentes"><p>Clases en la escena · usa la lista para seleccionar vehículos pequeños</p>
 <ul>{classes.map(p=><li key={p.key}><i className="class-swatch" style={{backgroundColor:p.color}} aria-hidden="true"/>{p.label}</li>)}</ul></div>;
}
