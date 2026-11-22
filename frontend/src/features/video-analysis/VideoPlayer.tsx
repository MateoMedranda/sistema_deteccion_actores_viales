import {useEffect,useRef,useState} from "react";
import {ClientError,type ApiClient} from "../../services/apiClient";
import type {VideoJob} from "./videoTypes";
export function VideoPlayer({client,job,active=true,onUnavailable}:{client:ApiClient;job:VideoJob;active?:boolean;onUnavailable?:()=>void}){
 const video=useRef<HTMLVideoElement>(null),alive=useRef(true),[failed,setFailed]=useState(false),[retired,setRetired]=useState(false),[attempt,setAttempt]=useState(0);
 const url=client.nativeVideo(job.job_id);
 const request=useRef(new AbortController());
 useEffect(()=>{alive.current=true;request.current=new AbortController();setFailed(false);setRetired(false);
  let timer:ReturnType<typeof setTimeout>;
  const expire=()=>{const left=Date.parse(job.expires_at)-Date.now();if(left<=0){setRetired(true);onUnavailable?.();}else timer=setTimeout(expire,Math.min(2147483647,left));};expire();
  const node=video.current;
  if(node&&Date.parse(job.expires_at)>Date.now()&&node.getAttribute("src")!==url){node.setAttribute("src",url);node.load();}
  return()=>{alive.current=false;request.current.abort();clearTimeout(timer);if(node){node.pause();node.removeAttribute("src");node.load();}};
 },[client,job.job_id,job.expires_at,attempt]);
 useEffect(()=>{if(!active)video.current?.pause();},[active]);
 const failure=async()=>{
  const controller=request.current;
  try{await client.video(job.job_id,{timeoutMs:10000,expiresAt:job.expires_at,signal:controller.signal});if(alive.current&&!controller.signal.aborted)setFailed(true);}
  catch(error){if(!alive.current||controller.signal.aborted)return;if(error instanceof ClientError&&[401,403,404,410].includes(error.status)){setRetired(true);onUnavailable?.();}else setFailed(true);}
 };
 return <section className="video-player" aria-label="Video analizado">{!retired&&!failed&&<video key={attempt} ref={video} className="result-video" controls preload="metadata" playsInline src={url} onError={()=>void failure()} aria-label="Video analizado con contornos por clase"/>}{retired?<p role="status">El video ya no está disponible.</p>:failed?<div role="alert"><p>No se pudo reproducir el video. El análisis sigue disponible.</p><button onClick={()=>{setFailed(false);setAttempt(attempt+1);}}>Reintentar reproducción</button></div>:<p className="muted">Pausa o recorre el video para revisar la escena. Las fichas muestran evidencia representativa del análisis.</p>}</section>;
}
