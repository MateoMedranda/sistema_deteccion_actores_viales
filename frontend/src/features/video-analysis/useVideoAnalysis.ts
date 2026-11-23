import {useEffect,useReducer,useRef} from "react";
import {ApiClient,ClientError,type RequestOptions} from "../../services/apiClient";
import {parseVideoJob,type VideoJob} from "./videoTypes";
import type {EnrichmentJob} from "../../services/apiTypes";
import {initialVideoState,videoAnalysisReducer,type EnrichmentState,type VideoAction} from "./videoAnalysisReducer";
type Timer=ReturnType<typeof setTimeout>;
type Intent={intent:string;intentGeneration?:number};
type Context={generation:number;controller:AbortController;enrichController:AbortController;file?:File;video?:VideoJob;videoId?:string;enrichId?:string;uploadIntent?:Intent;enrichIntent?:Intent;busy:boolean;enrichBusy:boolean;autoStarted:boolean;enrichPhase:EnrichmentState;videoPoll?:Timer;enrichPoll?:Timer;videoExpiry?:Timer;enrichExpiry?:Timer;enriched?:EnrichmentJob};
const context=(generation:number,file?:File):Context=>({generation,file,controller:new AbortController(),enrichController:new AbortController(),busy:false,enrichBusy:false,autoStarted:false,enrichPhase:"waiting"});
const identifier=(value:unknown):string=>{if(typeof value!=="string"||!/^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(value))throw Error("invalid_receipt");return value;};
export function useVideoAnalysis(client?:ApiClient,progressive=false){
 const [state,dispatch]=useReducer(videoAnalysisReducer,initialVideoState);
 const ref=useRef(context(0)),alive=useRef(true);
 const current=(c:Context)=>alive.current&&ref.current===c&&!c.controller.signal.aborted;
 type Payload<T> = T extends {generation:number}?Omit<T,"generation">:never;
 const send=(c:Context,action:Payload<VideoAction>)=>{if(alive.current&&ref.current===c)dispatch({...action,generation:c.generation} as VideoAction);};
 const clear=(c:Context)=>{for(const key of ["videoPoll","enrichPoll","videoExpiry","enrichExpiry"] as const)if(c[key])clearTimeout(c[key]);};
 const retire=(c:Context,scope:"source"|"enrichment")=>{
  if(ref.current!==c)return;
  if(scope==="source"){clear(c);c.controller.abort();c.enrichController.abort();c.file=undefined;c.video=undefined;c.videoId=undefined;c.enrichId=undefined;}
  else{if(c.enrichPoll)clearTimeout(c.enrichPoll);c.enrichController.abort();c.enrichId=undefined;c.enriched=undefined;c.enrichPhase="expired";}
  send(c,{type:"retire",scope});
 };
 const knownCancel=(c:Context)=>{
  if(c.videoId){
   if(progressive)void client?.withdrawPlayback(c.videoId).catch(()=>{});
   else if(c.video?.status!=="completed")void client?.cancelVideo(c.videoId).catch(()=>{});
  }
  if(c.enrichId&&!["completed","failed","cancelled"].includes(c.enrichPhase))void client?.cancelEnrichment(c.enrichId,{timeoutMs:5000}).catch(()=>{});
 };
 useEffect(()=>{alive.current=true;return()=>{alive.current=false;const c=ref.current;clear(c);c.controller.abort();c.enrichController.abort();knownCancel(c);};},[client]);
 const error=(c:Context,cause:unknown,scope:"source"|"enrichment")=>{
  if(ref.current!==c||!alive.current)return;
  if(cause instanceof ClientError&&[401,403,404,410].includes(cause.status)){retire(c,scope);return;}
  const code=cause instanceof ClientError?cause.detail.code:"invalid_response";
  const network=!(cause instanceof ClientError)||cause.status===0||["request_timeout","network_unavailable"].includes(code);
  if(scope==="enrichment"&&cause instanceof ClientError&&cause.status===400&&code==="no_eligible_vehicles"){
   c.enrichPhase="not_applicable";send(c,{type:"enrichment",value:"not_applicable"});return;
  }
  if(scope==="source")send(c,{type:"processing",value:network?"interrupted":"failed"});
  else{c.enrichPhase=network?"interrupted":"failed";send(c,{type:"enrichment",value:c.enrichPhase});}
  send(c,{type:"message",value:network?"La conexión se interrumpió. Reanuda para comprobar el mismo trabajo.":"La etapa no pudo completarse. Puedes reintentar mientras la fuente siga vigente."});
 };
 const expiry=(c:Context,scope:"source"|"enrichment",at:number)=>{
  const key=scope==="source"?"videoExpiry":"enrichExpiry";
  if(c[key])clearTimeout(c[key]);
  const check=()=>{if(ref.current!==c||!alive.current)return;const left=at-Date.now();if(left<=0)retire(c,scope);else c[key]=setTimeout(check,Math.min(2147483647,left));};
  check();
 };
 const scheduleVideo=(c:Context)=>{if(c.videoPoll)clearTimeout(c.videoPoll);c.videoPoll=setTimeout(()=>void pollVideo(c),1200);};
 const scheduleEnrich=(c:Context,id:string)=>{if(c.enrichPoll)clearTimeout(c.enrichPoll);c.enrichPoll=setTimeout(()=>void pollEnrichment(c,id),1200);};
 const pollEnrichment=async(c:Context,id:string)=>{
  const signal=c.enrichController.signal;
  if(!client||!current(c)||c.enrichId!==id||c.enrichController.signal.aborted)return;
  try{
   const job=await client.enrichment(id,{signal,timeoutMs:10000,expiresAt:c.video?.expires_at});
   if(!current(c)||c.enrichId!==id||signal.aborted)return;
   if(job.source.kind!=="video"||job.source.source_id!==c.videoId||job.enrichment_job_id!==id)throw Error("invalid_identity");
   if(Date.parse(job.expires_at)<=Date.now()){retire(c,"enrichment");return;}
   c.enriched=job;c.enrichPhase=job.status as EnrichmentState;
   send(c,{type:"enriched",value:job});send(c,{type:"enrichment",value:c.enrichPhase});
   if(c.enrichExpiry)clearTimeout(c.enrichExpiry);
   expiry(c,"enrichment",Math.min(Date.parse(job.expires_at),Date.parse(c.video!.expires_at)));
   if(["queued","processing"].includes(job.status))scheduleEnrich(c,id);
  }catch(cause){if(current(c)&&!signal.aborted)error(c,cause,"enrichment");}
 };
 const submitEnrichment=async(c:Context)=>{
  const signal=c.enrichController.signal;
  if(!client||!current(c)||!c.videoId||c.video?.status!=="completed"||c.enrichBusy)return;
  c.enrichBusy=true;c.enrichPhase="submitting";
  c.enrichIntent??=client.newVideoIntent();
  send(c,{type:"enrichment",value:"submitting"});
  try{
   const receipt=await client.enrich("video",c.videoId,{...c.enrichIntent,signal,timeoutMs:15000,expiresAt:c.video.expires_at});
   const id=identifier(receipt.enrichment_job_id);
   if(!current(c)||signal.aborted){void client.cancelEnrichment(id,{timeoutMs:5000}).catch(()=>{});return;}
   c.enrichId=id;await pollEnrichment(c,id);
  }catch(cause){if(current(c)&&!signal.aborted)error(c,cause,"enrichment");}
  finally{c.enrichBusy=false;}
 };
 const pollVideo=async(c:Context)=>{
  const signal=c.controller.signal;
  if(!client||!current(c)||!c.videoId)return;
  try{
   const job=parseVideoJob(await client.video(c.videoId,{signal,timeoutMs:10000}));
   if(!current(c)||signal.aborted||job.job_id!==c.videoId)return;
   if(Date.parse(job.expires_at)<=Date.now()){retire(c,"source");return;}
   c.video=job;send(c,{type:"video",value:job});if(progressive)send(c,{type:"message",value:""});
   if(c.videoExpiry)clearTimeout(c.videoExpiry);
   expiry(c,"source",Date.parse(job.expires_at));
   if(job.status==="completed"){
    send(c,{type:"processing",value:"ready"});send(c,{type:"media",value:"available"});
    send(c,{type:"message",value:"Video disponible. Puedes reproducirlo mientras consultamos los vehículos."});
    if(progressive){c.autoStarted=true;}
    else if(job.eligible_track_count===0){c.enrichPhase="not_applicable";send(c,{type:"enrichment",value:"not_applicable"});}
    else if(job.processing_phase==="ready"&&job.eligible_track_count!==null&&job.eligible_track_count>0&&!c.autoStarted){c.autoStarted=true;await submitEnrichment(c);}
   }else{
    send(c,{type:"processing",value:job.status});
    if(["queued","processing"].includes(job.status))scheduleVideo(c);
   }
  }catch(cause){if(current(c)&&!signal.aborted)error(c,cause,"source");}
 };
 const choose=(file?:File)=>{
  const old=ref.current;clear(old);old.controller.abort();old.enrichController.abort();knownCancel(old);
  const next=context(old.generation+1,file);ref.current=next;
  dispatch({type:"reset",generation:next.generation,file});
 };
 const start=async()=>{
  const c=ref.current;
  const signal=c.controller.signal;
  if(!client||!c.file||c.busy||c.videoId||!current(c))return;
  c.busy=true;c.uploadIntent??=client.newVideoIntent();
  send(c,{type:"processing",value:"uploading"});
  send(c,{type:"message",value:"Subiendo y validando el video…"});
  try{
   const receipt=await client.uploadVideo(c.file,{...c.uploadIntent,signal,timeoutMs:180000},progressive);
   const id=identifier(receipt.job_id);
   if(!current(c)||signal.aborted){void (progressive?client.withdrawPlayback(id):client.cancelVideo(id)).catch(()=>{});return;}
   c.videoId=id;send(c,{type:"processing",value:"checking"});await pollVideo(c);
  }catch(cause){if(current(c)&&!signal.aborted)error(c,cause,"source");}
  finally{c.busy=false;}
 };
 const resume=async()=>{
  const c=ref.current;
  if(c.controller.signal.aborted&&c.file){c.controller=new AbortController();}
  if(c.videoId&&c.video?.status!=="completed")await pollVideo(c);
  else if(c.enrichId){if(c.enrichController.signal.aborted)c.enrichController=new AbortController();await pollEnrichment(c,c.enrichId);}
  else if(c.enrichIntent){if(c.enrichController.signal.aborted)c.enrichController=new AbortController();await submitEnrichment(c);}
  else if(!c.videoId)await start();
 };
 const retryEnrichment=async()=>{
  const c=ref.current;
  if(!client||!current(c)||!c.video||Date.parse(c.video.expires_at)<=Date.now()||!["failed","cancelled","expired"].includes(c.enrichPhase))return;
  if(c.enrichPoll)clearTimeout(c.enrichPoll);if(c.enrichExpiry)clearTimeout(c.enrichExpiry);
  c.enrichController.abort();c.enrichController=new AbortController();c.enrichId=undefined;c.enriched=undefined;c.enrichIntent=client.newVideoIntent();
  await submitEnrichment(c);
 };
 const cancel=async(scope:"processing"|"enrichment")=>{
  const c=ref.current;
  if(!client||!current(c))return;
  try{
   if(scope==="processing"){
    if(c.videoPoll)clearTimeout(c.videoPoll);
    if(c.videoId){c.controller.abort();c.controller=new AbortController();if(progressive){await client.withdrawPlayback(c.videoId);retire(c,"source");}else{await client.cancelVideo(c.videoId);await pollVideo(c);}}
    else{c.controller.abort();send(c,{type:"processing",value:"interrupted"});send(c,{type:"message",value:"Solicitud interrumpida. Reanuda para comprobar si fue aceptada."});}
   }else{
    if(c.enrichPoll)clearTimeout(c.enrichPoll);
    if(c.enrichId){c.enrichController.abort();c.enrichController=new AbortController();await client.cancelEnrichment(c.enrichId,{timeoutMs:5000});await pollEnrichment(c,c.enrichId);}
    else{c.enrichController.abort();c.enrichPhase="interrupted";send(c,{type:"enrichment",value:"interrupted"});}
   }
  }catch(cause){if(cause instanceof ClientError&&cause.status===409){if(scope==="processing")await pollVideo(c);else if(c.enrichId)await pollEnrichment(c,c.enrichId);}else error(c,cause,scope==="processing"?"source":"enrichment");}
 };
 const retryVideo=async()=>{const file=ref.current.file;if(!file)return;choose(file);await start();};
 const rejectFile=(message:string)=>{ref.current.file=undefined;send(ref.current,{type:"message",value:message});dispatch({type:"reset",generation:ref.current.generation+1});ref.current.generation++;send(ref.current,{type:"message",value:message});};
 const discard=()=>retire(ref.current,"source");
 return {state,choose,start,resume,retryEnrichment,cancel,retryVideo,rejectFile,discard,mediaError:()=>{const c=ref.current;send(c,{type:"media",value:"failed"});if(c.videoId)void pollVideo(c);}};
}
