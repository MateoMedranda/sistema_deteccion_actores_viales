import {useCallback,useEffect,useRef,useState} from 'react';
import {ApiClient,ClientError} from '../../services/apiClient';import type {Playback} from './progressiveTypes';import type {CountLine} from './useProgressiveCount';
import {parseDetail,type DirectedCount} from './inspectionContracts';import type {CountDirection} from './directionArrow';
export function useDirectedCount(client:ApiClient,id:string,state:Playback|undefined,position:number,active:boolean,onUnavailable:()=>void){
 const [result,setResult]=useState<DirectedCount>(),[message,setMessage]=useState('');const current=useRef<DirectedCount>();
 const refs=useRef({state,position,active,onUnavailable});refs.current={state,position,active,onUnavailable};const sequence=useRef(0),controller=useRef(new AbortController());
 const path='/api/v1/video-jobs/'+id+'/playback/directed-count';
 const fail=(error:unknown)=>{if(error instanceof ClientError&&[401,403,404,410].includes(error.status))refs.current.onUnavailable();else setMessage('No se pudo aplicar o consultar el conteo. Conservamos la configuración confirmada.');};
 const read=useCallback(async()=>{
  const {state:s,position:p}=refs.current,c=controller.current,version=++sequence.current;if(!s||c.signal.aborted)return;
  const us=Math.min(Math.round(p),s.last_frame_start_us??0);
  try{
   const value=parseDetail<DirectedCount>('DirectedCount',await client.json(path+'?generation='+s.generation+'&at_us='+us,undefined,{signal:c.signal,timeoutMs:10000,expiresAt:s.expires_at}));
   if(c.signal.aborted||version!==sequence.current)return;
   if(value.job_id!==id||value.generation!==s.generation||value.at_us!==us)throw Error('count_context_mismatch');
   current.current=value;setResult(value);setMessage(value.status==='pending'?'Calculando cruces del tramo confirmado…':'');return value;
  }catch(e){if(!c.signal.aborted)fail(e)}
 },[client,id,path]);
 useEffect(()=>{const c=new AbortController();controller.current=c;current.current=undefined;setResult(undefined);let timer:ReturnType<typeof setTimeout>;
 const poll=async()=>{if(c.signal.aborted)return;if(refs.current.active&&!document.hidden)await read();if(!c.signal.aborted)timer=setTimeout(poll,400)};void poll();return()=>{c.abort();clearTimeout(timer);sequence.current++};
 },[client,id,state?.generation,read]);
 const configure=async(line:CountLine,direction:CountDirection='negative_to_positive')=>{
  const s=refs.current.state;if(!s)return;const c=controller.current;const before=await read();if(!before)return;
  try{
   const value=parseDetail<DirectedCount>('DirectedCount',await client.json(path,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({generation:s.generation,expected_revision:before.revision,line,direction})},{signal:c.signal,timeoutMs:15000,expiresAt:s.expires_at}));
   if(c.signal.aborted)return;current.current=value;setResult(value);await read();
  }catch(e){if(!c.signal.aborted){await read();fail(e)}}
 };
 const disable=async()=>{const s=refs.current.state;if(!s)return;const before=await read();if(!before)return;try{await client.json(path+'?generation='+s.generation+'&expected_revision='+before.revision,{method:'DELETE'},{signal:controller.current.signal,timeoutMs:10000,expiresAt:s.expires_at});await read()}catch(e){await read();fail(e)}};
 const refresh=(at?:number)=>{if(at!==undefined)refs.current.position=at;sequence.current++;setResult(value=>value?{...value,status:'pending',total:null}:value);void read()};
 return {result,message,configure,disable,refresh};
}
