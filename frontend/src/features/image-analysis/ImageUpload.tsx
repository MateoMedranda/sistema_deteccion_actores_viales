import type {ImagePolicy} from "../../services/apiTypes";
import {MediaUpload} from "../../components/MediaUpload";
export function ImageUpload({disabled,file,preview,generation,onChoose,onAnalyze,onReset,compact,policy,policyFailed}:{
 policy?:ImagePolicy;policyFailed?:boolean;compact?:boolean;disabled:boolean;file?:File;preview:string;generation:number;
 onChoose:(file?:File)=>void;onAnalyze:()=>void;onReset:()=>void;
}){
 return <MediaUpload kind="image" title="Tu imagen, lista para explorar" description="Vehículos, atributos y placas en un solo análisis." inputLabel="Seleccionar imagen" selectLabel="Seleccionar imagen" actionLabel="Analizar imagen" clearLabel="Limpiar imagen" accept="image/jpeg,image/png" disabled={disabled} file={file} preview={preview} generation={generation} onChoose={onChoose} onAnalyze={onAnalyze} onReset={onReset} compact={compact}
 hint={<><small>JPEG o PNG · Archivos temporales y privados</small><small>{policy
 ? "Máximo "+new Intl.NumberFormat("es",{maximumFractionDigits:2}).format(policy.max_upload_bytes/1024/1024)+" MiB y "+new Intl.NumberFormat("es",{maximumFractionDigits:2}).format(policy.max_image_pixels/1000000)+" MP ("+policy.max_image_pixels.toLocaleString("es")+" píxeles)."
 :policyFailed?"No se pudieron consultar los límites; el servicio validará el archivo.":"Preparando los límites de carga automáticamente…"}</small></>}/>;
}
