import type {VehicleResult} from "../../services/apiTypes";
import type {VideoMetadata} from "./videoTypes";
import {plateStateLabel} from "./VideoTrackList";
import {classPresentation} from "../image-analysis/classPresentation";
export function VideoTrackDetails({item,metadata,onClose}:{item?:VehicleResult;metadata:VideoMetadata|null;onClose?:()=>void}){
 const frame=(i:number)=>"Cuadro "+i+(metadata?" · "+(i/metadata.fps).toFixed(2)+" s del video procesado":"");
 const references=(indexes?:number[])=>indexes?.length?<ul className="evidence-references">{indexes.map(i=><li key={i}>{frame(i)}</li>)}</ul>:<p className="muted">Referencia temporal no informada.</p>;
 return <aside id="video-track-details" className="vehicle-details video-track-details" aria-label="Ficha de trayectoria">
 {!item?<div className="details-empty"><h3>Explora una trayectoria</h3><p>Selecciona un vehículo de la lista para consultar sus atributos y la evidencia de su placa.</p></div>:<>
 <div className="details-heading"><div><span className="eyebrow">FICHA DEL VEHÍCULO</span><h3>Trayectoria {item.track_id}</h3></div>{onClose&&<button className="icon-button" aria-label="Cerrar ficha de trayectoria" onClick={onClose}>×</button>}</div>
 <p>{classPresentation(item.class_name).label}</p><p className="confidence-note">El ID identifica esta trayectoria dentro de este video.</p>
 <section className="detail-section"><h4>Atributos</h4>{item.attributes_status==="failed"?<p>Los atributos no están disponibles.</p>:item.attributes.length?<dl className="attribute-list">{item.attributes.map((a,i)=><div key={a.name+":"+i}><dt>{a.name}</dt><dd>{a.label} <small>{Math.round(a.confidence*100)}% de confianza</small>{a.evidence_frame_index!=null&&<small className="attribute-evidence">{frame(a.evidence_frame_index)}</small>}</dd></div>)}</dl>:<p>Sin atributos informados.</p>}</section>
 <section className="detail-section"><h4>Placa</h4><span className={"plate-status plate-"+item.plate_status}>{plateStateLabel[item.plate_status]}</span>{item.plate_status==="read"&&<p className="plate-text">{item.plate.text}</p>}
 {item.plate.localizer_confidence!=null&&<p className="muted">Localización: {Math.round(item.plate.localizer_confidence*100)}% de confianza</p>}
 {item.plate.ocr_confidence!=null&&<p className="muted">Lectura: {Math.round(item.plate.ocr_confidence*100)}% de confianza</p>}
 {item.plate.provenance?<p className="muted">Origen de lectura: {({"raw":"original","legacy-retry-v1":"tratamiento de lectura","bilateral-clahe-v1":"contraste local","bilateral-adaptive-v1":"contraste adaptativo","unknown":"desconocido","none":"sin lectura seleccionada"} as Record<string,string>)[item.plate.provenance.selected_variant]??"variante informada"}</p>:<p className="muted">Procedencia no informada.</p>}
 {references(item.plate.evidence_frame_indexes)}</section>
 <section className="detail-section"><h4>Evidencia de la trayectoria</h4>{references(item.evidence_frame_indexes)}<p className="confidence-note">Estas referencias corresponden a la evidencia analizada; no describen necesariamente el instante que estás reproduciendo. No hay recortes de video disponibles.</p></section>
 </>}
 </aside>;
}
