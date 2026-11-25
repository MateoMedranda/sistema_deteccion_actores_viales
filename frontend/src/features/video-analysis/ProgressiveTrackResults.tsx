import {VehicleDetailsCard} from "../../components/vehicle-details/VehicleDetailsCard";
import {classPresentation} from "../image-analysis/classPresentation";
import {useEffect,useState} from "react";
import {ApiClient,ClientError} from "../../services/apiClient";
import type {Track} from "./progressiveTypes";
import {clock} from "./VideoTimeline";
const states:Record<string,string>={not_requested:"Selecciona el vehículo para consultar sus datos",waiting_evidence:"Preparando evidencia",queued:"Consulta en cola",processing:"Consultando atributos y placa…",ready:"Datos disponibles",partial:"Datos parciales",failed:"No se pudo completar la consulta",not_applicable:"Enriquecimiento no aplicable"};
const plateStates:Record<string,string>={pending:"Consultando placa…",read:"Placa leída",unreadable:"Placa ilegible",not_detected:"Placa no detectada",failed:"No se pudo consultar la placa",not_applicable:"Lectura no aplicable"};
function Crop({client,path,label,expiry,onUnavailable}:{client:ApiClient;path:string;label:string;expiry:string;onUnavailable:()=>void}){
 const [url,setUrl]=useState<string>(),[failed,setFailed]=useState(false);
 useEffect(()=>{const c=new AbortController();let object:string|undefined,timer:ReturnType<typeof setTimeout>,attempt=0;
 const load=async()=>{try{const b=await client.blob(path,{signal:c.signal,expiresAt:expiry,timeoutMs:10000});if(c.signal.aborted)return;object=URL.createObjectURL(b);setUrl(object);setFailed(false)}catch(e){if(c.signal.aborted)return;if(e instanceof ClientError&&[401,403,404,410].includes(e.status)){onUnavailable();return}setFailed(true);timer=setTimeout(load,Math.min(8000,1000*2**attempt++))}};
 void load();return()=>{c.abort();clearTimeout(timer);if(object)URL.revokeObjectURL(object);setUrl(undefined)};
 },[client,path,expiry]);
 return <figure className="video-evidence"><figcaption>{label}</figcaption>{url?<img src={url} alt={label}/>:<p className="muted">{failed?"Recuperando el recorte…":"Preparando el recorte…"}</p>}</figure>;
}
export function ProgressiveTrackList({observations,selected,onSelect}:{observations:{track_id:number;class_name:string}[];selected?:number;onSelect:(id:number)=>void}){
 return <div className="progressive-track-list">{observations.map(t=><button key={t.track_id} aria-pressed={selected===t.track_id} onClick={()=>onSelect(t.track_id)}><i className="class-swatch" style={{backgroundColor:classPresentation(t.class_name).color}} aria-hidden="true"/>#{t.track_id} · {classPresentation(t.class_name).label}</button>)}</div>;
}
export function ProgressiveTrackResults({client,tracks,selected,onSelect,onUnavailable,onClose,requestMessage}:{client:ApiClient;tracks:Track[];selected?:number;onSelect:(id:number)=>void;onUnavailable:()=>void;onClose?:()=>void;requestMessage?:string}){
 const track=tracks.find(t=>t.track_id===selected),pending=track&&["waiting_evidence","queued","processing"].includes(track.state);
 const plateEvidence=track?.evidence.find(e=>e.plate_url&&track.plate.evidence_ids.includes(e.evidence_id));
 const vehicle=track?.evidence[0];
 return <VehicleDetailsCard className="progressive-details">
 {!track?<div className="details-empty"><span aria-hidden="true">⌖</span><h3>Explora cada vehículo</h3><p>{selected?"Preparando la ficha del vehículo seleccionado…":"Pausa y selecciona un recuadro del video para consultar atributos, placa y recortes."}</p><p className="muted">Solo se consultan los vehículos que selecciones.</p></div>:<>
 <div className="details-heading"><div><span className="eyebrow">FICHA DEL VEHÍCULO</span><h3>Vehículo #{track.track_id}</h3></div><button className="icon-button" aria-label="Cerrar ficha del vehículo" onClick={onClose}>×</button></div>
 <div className="vehicle-meta"><span><i className="class-swatch" style={{backgroundColor:classPresentation(track.class_name).color}} aria-hidden="true"/>{classPresentation(track.class_name).label}</span><span>Track ID {track.track_id}</span></div>
 <p role="status" className="muted">{requestMessage||states[track.state]||"Datos no disponibles"}</p>
 {vehicle&&<><Crop client={client} path={vehicle.vehicle_url!} label="Recorte del vehículo" expiry={vehicle.expires_at} onUnavailable={onUnavailable}/><p className="confidence-note">Evidencia representativa de {clock(vehicle.time_us)} · no cambia la reproducción.</p></>}
 <div className="detail-section"><h4>Atributos</h4>{track.attributes.items.length?<dl className="attribute-list">{track.attributes.items.map(a=><div key={a.name}><dt>{({color:"Color",type:"Tipo",make:"Marca",model:"Modelo"} as Record<string,string>)[a.name]??a.name}</dt><dd>{a.value}<small>{Math.round(a.confidence*100)}%</small></dd></div>)}</dl>:<p className="muted">{track.state==="not_requested"?"Se consultarán al seleccionar este vehículo.":pending?"Consultando atributos…":track.attributes.status==="not_applicable"?"Atributos no aplicables.":track.attributes.status==="failed"?"No se pudieron consultar los atributos.":"Sin atributos disponibles."}</p>}</div>
 <div className="detail-section"><h4>Placa</h4><span className={"plate-status plate-"+track.plate.status}>{track.state==="not_requested"?"Sin consultar":plateStates[track.plate.status]??"Placa no disponible"}</span>{track.plate.text&&<div className="plate-text">{track.plate.text}</div>}{plateEvidence&&<><Crop client={client} path={plateEvidence.plate_url!} label="Recorte original de la placa" expiry={plateEvidence.expires_at} onUnavailable={onUnavailable}/><p className="confidence-note">Evidencia de {clock(plateEvidence.time_us)}</p></>}{track.plate.ocr_confidence!==null&&<p className="confidence-note">Confianza de lectura: {Math.round(track.plate.ocr_confidence*100)}%</p>}</div>
 {track.state==="not_requested"&&<button onClick={()=>onSelect(track.track_id)}>Consultar vehículo</button>}
 <p className="privacy-note">{track.final?"Consulta guardada temporalmente":"Datos provisionales · pueden actualizarse"} · Track ID local a este video.</p>
 </>}
 </VehicleDetailsCard>;
}
