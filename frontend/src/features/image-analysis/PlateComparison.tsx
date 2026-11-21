import type {Detection,VehicleResult} from "../../services/apiTypes";
import {ApiClient} from "../../services/apiClient";
import {plateCrop} from "../../utils/imageGeometry";
import {EvidenceCrop} from "./EvidenceCrop";
import {usePlatePreview} from "./usePlatePreview";
const readingVariants:Record<string,string>={raw:"Original","legacy-retry-v1":"Reintento con contraste","bilateral-clahe-v1":"Rescate con contraste local","bilateral-adaptive-v1":"Rescate con umbral adaptativo",none:"Sin lectura publicada"};
export function PlateComparison({client,sourceId,jobId,detection,result,original,expiresAt,onRejected}:{
 client?:ApiClient;sourceId:string;jobId?:string;detection:Detection;result?:VehicleResult;original:string;expiresAt?:number;onRejected?:(error:unknown)=>void;
}){
 const box=result?.plate.status!=="not_detected"?plateCrop(detection.bbox,result?.plate.bbox_relative):undefined;
 const context=original&&box&&jobId&&expiresAt?{sourceId,jobId,detectionId:detection.detection_id,box,expiresAt}:undefined;
 const preview=usePlatePreview(client,context,onRejected),processed=preview.view==="processed"&&preview.status==="available";
 return <div className="plate-comparison">
  <div className="comparison-controls" aria-label="Versión de la placa">
   <button aria-pressed={!processed} onClick={()=>preview.setView("original")}>Original</button>
   <button aria-pressed={processed} disabled={preview.status!=="available"} onClick={()=>preview.setView("processed")}>Procesada</button>
  </div>
  <div className="plate-inspection" role="region" aria-label="Inspección de placa" tabIndex={0}>
   <div hidden={processed}><EvidenceCrop original={original} box={box} label="Recorte de la placa" identity={sourceId+":"+detection.detection_id+":"+JSON.stringify(box)} zoom={preview.zoom}/></div>
   {processed&&<figure className="evidence plate-evidence"><figcaption>Placa procesada · contraste local</figcaption><img src={preview.url} alt="Versión procesada de la placa" style={{width:preview.zoom*100+"%",maxWidth:"none",maxHeight:"none",height:"auto"}}/></figure>}
  </div>
  <div className="comparison-controls" aria-label="Ampliación de placa">{([1,2,4] as const).map(z=><button key={z} aria-pressed={preview.zoom===z} onClick={()=>preview.setZoom(z)}>{z}x</button>)}</div>
  <p className="preview-status" role="status">{preview.status==="preparing"?"Preparando versión procesada…":preview.status==="available"?"Versión procesada disponible":preview.status==="not_applicable"?"El tratamiento no es aplicable a esta placa.":preview.status==="failed"?"No se pudo preparar la versión procesada. El original sigue disponible.":preview.status==="expired"?"La versión procesada venció.":"Sin versión procesada: se requiere una placa localizada y un original disponible."}</p>
  {preview.status==="failed"&&<button className="secondary" onClick={preview.retry}>Reintentar versión procesada</button>}
  <p className="confidence-note">Origen de lectura: {result?.plate.provenance&&result.plate.provenance.policy_id!=="legacy-unknown"?readingVariants[result.plate.provenance.selected_variant]:"Desconocido"}.
   {result?.plate.provenance&&result.plate.provenance.attempted_variants.length>0&&" Intentos: "+result.plate.provenance.attempted_variants.map(v=>readingVariants[v]).join(" · ")+"."}</p>
  <p className="confidence-note">Visualización: contraste local y ampliación cuando corresponde. Ampliar no recupera caracteres ausentes.</p>
 </div>;
}
