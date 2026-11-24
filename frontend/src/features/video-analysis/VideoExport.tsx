import {useEffect, useRef, useState} from "react";
import {ApiClient, ClientError} from "../../services/apiClient";
import "./VideoExport.css";

type ExportState = "waiting" | "queued" | "rendering" | "encoding" | "ready" | "failed";
type Receipt = {job_id:string;state:ExportState;processed_frames:number;total_frames:number;expires_at:string;url:string|null;error_code:string|null};
const busyStates = new Set(["queued", "rendering", "encoding"]);

function receipt(value:unknown,id:string):Receipt {
  const r=value as Receipt;
  if(!r||r.job_id!==id||!["waiting","queued","rendering","encoding","ready","failed"].includes(r.state)
    ||!Number.isSafeInteger(r.processed_frames)||!Number.isSafeInteger(r.total_frames)
    ||r.processed_frames<0||r.total_frames<r.processed_frames||!Number.isFinite(Date.parse(r.expires_at))
    ||(r.state==="ready"&&r.url!==`/api/v1/video-jobs/${id}/annotated-video/content`))throw new Error("invalid_export_state");
  return r;
}

export function VideoExport({client,id,enabled,serverState,active,expiresAt,onUnavailable}:{
  client:ApiClient;id:string;enabled:boolean;serverState:string;active:boolean;expiresAt:string;onUnavailable:()=>void;
}) {
  const [result,setResult]=useState<Receipt>();
  const [requested,setRequested]=useState(false);
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState("");
  const action=useRef<AbortController>();
  const unavailable=useRef(onUnavailable);unavailable.current=onUnavailable;
  const rejected=(e:unknown)=>e instanceof ClientError&&[401,403,404,410].includes(e.status);
  useEffect(()=>{
    const controller=new AbortController();action.current=controller;setBusy(false);
    return()=>controller.abort();
  },[client,id,active]);
  useEffect(()=>{
    if(!active||(!requested&&!["queued","encoding","ready","failed"].includes(serverState)))return;
    const controller=new AbortController();let timer:ReturnType<typeof setTimeout>;let failures=0;
    const poll=async()=>{
      try {
        const next=receipt(await client.json(`/api/v1/video-jobs/${id}/playback/export`,undefined,
          {signal:controller.signal,timeoutMs:10000,expiresAt}),id);
        if(controller.signal.aborted)return;
        setResult(next);setMessage("");failures=0;
        if(!busyStates.has(next.state)){setRequested(false);return;}
      } catch(e) {
        if(controller.signal.aborted)return;
        if(rejected(e)){unavailable.current();return;}
        failures++;setMessage("Recuperando el estado de la exportación…");
      }
      timer=setTimeout(poll,failures?Math.min(8000,1000*2**(failures-1)):500);
    };
    void poll();return()=>{controller.abort();clearTimeout(timer);};
  },[client,id,active,requested,serverState,expiresAt]);

  const request=async()=>{
    const controller=action.current;
    if(!controller||controller.signal.aborted||busy)return;
    setBusy(true);setMessage("");
    try {
      const next=receipt(await client.json(`/api/v1/video-jobs/${id}/playback/export`,{method:"POST"},
        {signal:controller.signal,timeoutMs:10000,expiresAt}),id);
      if(controller.signal.aborted)return;
      setResult(next);setRequested(busyStates.has(next.state));
    } catch(e) {
      if(controller.signal.aborted)return;
      if(rejected(e)){unavailable.current();return;}
      // A lost response may hide an accepted intent. GET checks the same job;
      // it never creates another export or repeats the POST automatically.
      setMessage("Comprobando si se recibió la solicitud…");setRequested(true);
    } finally {if(!controller.signal.aborted)setBusy(false);}
  };
  const state=result?.state??"waiting";
  const labels:Record<ExportState,string>={
    waiting:enabled?"El MP4 se preparará cuando lo solicites.":"Disponible al terminar el análisis.",
    queued:"Exportación en cola.",rendering:"Generando video anotado…",encoding:"Preparando el MP4 para descargar…",
    ready:"Video anotado listo para descargar.",failed:"No se pudo exportar. El análisis sigue disponible.",
  };
  return <section className="video-export" aria-label="Exportación del video">
    <div><h4>Video anotado</h4><p role="status">{message|| (busy?"Solicitando exportación…":labels[state])}</p>
      {result&&busyStates.has(state)&&<progress aria-label="Cuadros de la exportación" max={Math.max(1,result.total_frames)} value={result.processed_frames}/>}
    </div>
    {state==="ready"?<a href={client.nativeVideo(id)} download="video-anotado.mp4">Descargar MP4</a>:
      <button type="button" disabled={!active||!enabled||busy||busyStates.has(state)} onClick={()=>void request()}>
        {state==="failed"?"Reintentar exportación":"Exportar video anotado"}
      </button>}
  </section>;
}
