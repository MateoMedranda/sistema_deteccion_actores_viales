import {useCallback,useEffect,useRef,useState} from 'react';
import {ApiClient,ClientError} from '../../services/apiClient';
import type {Playback} from './progressiveTypes';
import type {CountLine} from './useProgressiveCount';
import {parseDetail,type DirectedCount} from './inspectionContracts';
import type {CountDirection} from './directionArrow';

function sameLine(a:CountLine|null,b:CountLine){return !!a&&a.point_a.x===b.point_a.x&&a.point_a.y===b.point_a.y&&a.point_b.x===b.point_b.x&&a.point_b.y===b.point_b.y}
export function useDirectedCount(client:ApiClient,id:string,state:Playback|undefined,position:number,active:boolean,onUnavailable:()=>void){
 const [result,setResult]=useState<DirectedCount>(),[message,setMessage]=useState('');
 const refs=useRef({state,position,active,onUnavailable});refs.current={state,position,active,onUnavailable};
 const sequence=useRef(0),controller=useRef(new AbortController()),mutating=useRef(false),mutations=useRef(Promise.resolve());
 const path='/api/v1/video-jobs/'+id+'/playback/directed-count';
 const fail=(error:unknown)=>{if(error instanceof ClientError&&[401,403,404,410].includes(error.status))refs.current.onUnavailable();else setMessage('No se pudo aplicar o consultar el conteo. Conservamos la configuración confirmada.')};
 const read=useCallback(async()=>{
  const {state:s,position:p}=refs.current,c=controller.current,version=++sequence.current;
  if(!s||c.signal.aborted)return;
  const us=Math.min(Math.round(p),s.last_frame_start_us??0);
  try{
   const value=parseDetail<DirectedCount>('DirectedCount',await client.json(path+'?generation='+s.generation+'&at_us='+us,undefined,{signal:c.signal,timeoutMs:10000,expiresAt:s.expires_at}));
   if(c.signal.aborted)return;
   if(value.job_id!==id||value.generation!==s.generation||value.at_us!==us)throw Error('count_context_mismatch');
   // A late position must not repaint the counter, but its revision can still
   // be used by the serialized mutation which explicitly requested this read.
   if(version===sequence.current){setResult(value);setMessage(value.status==='pending'?'Calculando cruces del tramo confirmado…':'')}
   return value;
  }catch(e){if(!c.signal.aborted)fail(e)}
 },[client,id,path]);
 useEffect(()=>{
  const c=new AbortController();controller.current=c;setResult(undefined);let timer:ReturnType<typeof setTimeout>;
  const poll=async()=>{if(c.signal.aborted)return;if(refs.current.active&&!document.hidden&&!mutating.current)await read();if(!c.signal.aborted)timer=setTimeout(poll,400)};
  void poll();return()=>{c.abort();clearTimeout(timer);sequence.current++};
 },[client,id,state?.generation,read]);
 const serialize=(action:()=>Promise<void>)=>{const task=mutations.current.then(async()=>{mutating.current=true;try{await action()}finally{mutating.current=false}});mutations.current=task.catch(()=>{});return task};
 const configure=(line:CountLine,direction:CountDirection='negative_to_positive')=>serialize(async()=>{
  const s=refs.current.state;if(!s)return;const c=controller.current,before=await read();if(!before||c.signal.aborted)return;
  try{
   const value=parseDetail<DirectedCount>('DirectedCount',await client.json(path,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({generation:s.generation,expected_revision:before.revision,line,direction})},{signal:c.signal,timeoutMs:15000,expiresAt:s.expires_at}));
   if(c.signal.aborted)return;
   if(value.job_id!==id||value.generation!==s.generation||value.direction!==direction||!sameLine(value.line,line))throw Error('count_context_mismatch');
   await read();
  }catch(e){if(!c.signal.aborted){const confirmed=await read();if(!confirmed||confirmed.direction!==direction||!sameLine(confirmed.line,line))fail(e)}}
 });
 const disable=()=>serialize(async()=>{
  const s=refs.current.state;if(!s)return;const c=controller.current,before=await read();if(!before||c.signal.aborted)return;
  try{await client.json(path+'?generation='+s.generation+'&expected_revision='+before.revision,{method:'DELETE'},{signal:c.signal,timeoutMs:10000,expiresAt:s.expires_at});await read()}
  catch(e){if(!c.signal.aborted){const confirmed=await read();if(!confirmed||confirmed.enabled)fail(e)}}
 });
 const refresh=(at?:number)=>{if(at!==undefined)refs.current.position=at;sequence.current++;setResult(value=>value?{...value,status:'pending',total:null}:value);void read()};
 return {result,message,configure,disable,refresh};
}
