import {useEffect,useState} from 'react';import type {ApiClient} from '../../services/apiClient';
export function InspectionEvidence({client,path,expiry,label,preview}:{client:ApiClient;path:string;expiry:string;label:string;preview?:{job:string;inspection:string;asset:string}}){
 const [url,setUrl]=useState<string>(),[failed,setFailed]=useState(false),[zoom,setZoom]=useState(1);
 useEffect(()=>{const c=new AbortController();let object:string|undefined;setFailed(false);
 const request=preview?client.inspectionPlatePreview(preview.job,preview.inspection,preview.asset,{signal:c.signal,expiresAt:expiry}).then(x=>x.blob):client.blob(path,{signal:c.signal,expiresAt:expiry,timeoutMs:10000});
 void request.then(blob=>{if(c.signal.aborted)return;object=URL.createObjectURL(blob);setUrl(object)}).catch(()=>{if(!c.signal.aborted)setFailed(true)});
 const timer=setTimeout(()=>{c.abort();setUrl(undefined);setFailed(true);if(object)URL.revokeObjectURL(object)},Math.min(2147483647,Math.max(0,Date.parse(expiry)-Date.now())));
 return()=>{clearTimeout(timer);c.abort();if(object)URL.revokeObjectURL(object)};
 },[client,path,expiry,preview?.job,preview?.inspection,preview?.asset]);
 return <figure className="video-evidence"><figcaption>{label}</figcaption>{url?<><div className="inspection-crop-viewport" tabIndex={0} aria-label={'Visor de '+label}><img src={url} alt={label} style={{width:zoom*100+'%',maxWidth:'none',maxHeight:zoom===1?260:'none'}}/></div>{/placa/i.test(label)&&<div className="progressive-controls">{[1,2,4].map(v=><button key={v} aria-pressed={zoom===v} onClick={()=>setZoom(v)}>{v}x</button>)}</div>}</>:<p className="muted">{failed?'Recorte no disponible en este contexto.':'Preparando el recorteâ€¦'}</p>}</figure>
}
