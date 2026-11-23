import {useCallback,useEffect,useRef,useState} from "react";
import {ApiClient,ClientError} from "../../services/apiClient";
import type {Playback} from "./progressiveTypes";
export type Point={x:number;y:number};
export type CountLine={point_a:Point;point_b:Point};
export type ProgressiveCount={job_id:string;generation:string;enabled:boolean;line:CountLine|null;revision:number;at_us:number;available_until_us:number;total:number;a_to_b:number;b_to_a:number};
export function useProgressiveCount(client:ApiClient,id:string,state:Playback|undefined,position:number,active:boolean,onUnavailable:()=>void){
 const [result,setResult]=useState<ProgressiveCount>(),[message,setMessage]=useState("");
 const refs=useRef({state,position,active,onUnavailable});refs.current={state,position,active,onUnavailable};
 const enabled=useRef(false),known=useRef(false),sequence=useRef(0),controller=useRef(new AbortController());
 const path="/api/v1/video-jobs/"+id+"/playback/count";
 const reject=(e:unknown)=>{if(e instanceof ClientError&&[401,403,404,410].includes(e.status))refs.current.onUnavailable();else setMessage("No se pudo actualizar el conteo. Reintentando automáticamente…")};
 const read=useCallback(async()=>{const {state:s,position:p}=refs.current,c=controller.current,version=++sequence.current;if(!s||!s.media_available||c.signal.aborted)return;
 const us=Math.min(Math.round(p),s.last_frame_start_us??0);
 try{const value=await client.json<ProgressiveCount>(path+"?at_us="+us,undefined,{signal:c.signal,timeoutMs:10000,expiresAt:s.expires_at});if(c.signal.aborted||version!==sequence.current)return;if(value.job_id!==id||value.generation!==s.generation||value.at_us!==us||![value.total,value.a_to_b,value.b_to_a,value.revision].every(n=>Number.isSafeInteger(n)&&n>=0))throw Error("invalid_count");enabled.current=value.enabled;known.current=true;setResult(value);setMessage("")}catch(e){if(!c.signal.aborted)reject(e)}
 },[client,id,path]);
 useEffect(()=>{const c=new AbortController();controller.current=c;enabled.current=false;known.current=false;setResult(undefined);let timer:ReturnType<typeof setTimeout>,busy=false;const poll=async()=>{if(c.signal.aborted)return;if(!busy&&refs.current.active&&!document.hidden&&(enabled.current||!known.current)){busy=true;await read();busy=false}if(!c.signal.aborted)timer=setTimeout(poll,500)};void poll();return()=>{c.abort();clearTimeout(timer);sequence.current++}},[client,id,state?.generation,read]);
 const configure=async(line:CountLine)=>{const s=refs.current.state,c=controller.current;if(!s)return;setMessage("Calculando cruces con las trayectorias disponibles…");try{await client.json(path,{method:"PUT",body:JSON.stringify(line),headers:{"Content-Type":"application/json"}},{signal:c.signal,timeoutMs:15000,expiresAt:s.expires_at});if(c.signal.aborted)return;enabled.current=true;await read()}catch(e){if(!c.signal.aborted){known.current=false;reject(e)}}};
 const disable=async()=>{const c=controller.current;try{await client.disableProgressiveCount(id,{signal:c.signal,timeoutMs:10000});if(c.signal.aborted)return;enabled.current=false;known.current=true;sequence.current++;setResult(undefined);setMessage("")}catch(e){if(!c.signal.aborted){known.current=false;reject(e)}}};
 const refresh=(at?:number)=>{if(at!==undefined)refs.current.position=at;sequence.current++;setResult(r=>r?{...r,at_us:-1}:r);if(enabled.current)void read()};
 return {result,message,configure,disable,refresh};
}
