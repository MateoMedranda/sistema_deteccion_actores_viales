import type {ImagePolicy} from "../../services/apiTypes";
import {useId} from "react";
export function ImageUpload({disabled,file,preview,generation,onChoose,onAnalyze,onReset,compact,policy,policyFailed}:{
 policy?:ImagePolicy;policyFailed?:boolean;compact?:boolean;disabled:boolean;file?:File;preview:string;generation:number;
 onChoose:(file?:File)=>void;onAnalyze:()=>void;onReset:()=>void;
}){
 const id=useId();
 return <div className={"upload-card image-upload-card"+(compact?" is-compact":"")}>
  <div className="upload-copy">
   <div className="upload-heading">
    <span className="upload-glyph" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1.4"/><path d="m3 17 5-5 4 4 4-6 5 7"/></svg></span>
    <div><h3>Tu imagen, lista para explorar</h3><p>Vehículos, atributos y placas en un solo análisis.</p></div>
   </div>
   <div className="upload-selection">
    <label className="file-label" htmlFor={id}>Seleccionar imagen<input key={generation} id={id} aria-label="Seleccionar imagen" type="file" accept="image/jpeg,image/png" onChange={e=>onChoose(e.target.files?.[0])}/></label>
    <div className="upload-hints"><small>JPEG o PNG · Archivos temporales y privados</small><small>{policy
     ? "Máximo "+new Intl.NumberFormat("es",{maximumFractionDigits:2}).format(policy.max_upload_bytes/1024/1024)+" MiB y "+new Intl.NumberFormat("es",{maximumFractionDigits:2}).format(policy.max_image_pixels/1000000)+" MP ("+policy.max_image_pixels.toLocaleString("es")+" píxeles)."
     :policyFailed?"No se pudieron consultar los límites; el servicio validará el archivo.":"Preparando los límites de carga automáticamente…"}</small></div>
   </div>
  </div>
  <div className="upload-review">
   <div className="upload-file-summary">
    {preview&&<img className="upload-preview" src={preview} alt="Vista previa de la imagen seleccionada"/>}
    <span className="filename" title={file?.name}>{file?.name??"Ningún archivo seleccionado"}</span>
   </div>
   <div className="upload-actions">
    {!compact&&<button className="primary" disabled={disabled||!file} onClick={onAnalyze}>Analizar imagen <span aria-hidden="true">→</span></button>}
    {file&&<button className="quiet" onClick={onReset}>Limpiar imagen</button>}
   </div>
  </div>
 </div>;
}
