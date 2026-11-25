import {useEffect,useRef,useState} from 'react';
import {ApiClient,ClientError} from '../../services/apiClient';
import {parseInspection,type Inspection} from './inspectionContracts';
export type InspectionSelection={generation:string;track_id:number;frame_index:number};
export function useVideoInspection(client:ApiClient,job:string,selection:InspectionSelection|undefined,onUnavailable:()=>void){
 const key=selection?[job,selection.generation,selection.track_id,selection.frame_index].join(':'):'';
 const [current,setCurrent]=useState<{key:string;result?:Inspection;message:string}>({key:'',message:''});
 const cache=useRef(new Map<string,Inspection>()),cacheTimers=useRef(new Map<string,ReturnType<typeof setTimeout>>());
 useEffect(()=>()=>{for(const timer of cacheTimers.current.values())clearTimeout(timer);cacheTimers.current.clear();cache.current.clear()},[]);const unavailable=useRef(onUnavailable);unavailable.current=onUnavailable;
 useEffect(()=>{
  if(!selection)return;
  const selected=selection,c=new AbortController();let timer:ReturnType<typeof setTimeout>,expiryTimer:ReturnType<typeof setTimeout>,attempt=0,result=cache.current.get(key);
  const base='/api/v1/video-jobs/'+job+'/playback/inspections';
  if(result&&Date.parse(result.expires_at)<=Date.now()){cache.current.delete(key);result=undefined}
  const publish=(v:Inspection)=>{if(c.signal.aborted)return;cache.current.set(key,v);clearTimeout(cacheTimers.current.get(key));cacheTimers.current.set(key,setTimeout(()=>{cache.current.delete(key);cacheTimers.current.delete(key)},Math.min(2147483647,Math.max(0,Date.parse(v.expires_at)-Date.now()))));if(cache.current.size>128)cache.current.delete(cache.current.keys().next().value!);setCurrent({key,result:v,message:''});clearTimeout(expiryTimer);expiryTimer=setTimeout(()=>{cache.current.delete(key);c.abort();setCurrent({key,message:'La consulta ha vencido. El video sigue disponible.'})},Math.min(2147483647,Math.max(0,Date.parse(v.expires_at)-Date.now())))};
  const request=async()=>{
   try{
    const raw=await client.json(result?base+'/'+result.inspection_id:base,result?undefined:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(selected)},{signal:c.signal,timeoutMs:10000,expiresAt:result?.expires_at});
    const v=parseInspection(raw,job,selected.generation,selected.track_id,selected.frame_index);result=v;publish(v);
    if(['queued','preparing','processing'].includes(v.state))timer=setTimeout(request,400);
   }catch(e){
    if(c.signal.aborted)return;
    if(e instanceof ClientError&&([401,403].includes(e.status)||(e.status===410&&e.detail.code==='artifact_expired'))){unavailable.current();return}
    if(e instanceof ClientError&&[404,410,409,422,429].includes(e.status)){setCurrent({key,message:e.status===410?'La consulta ha vencido. El video sigue disponible.':'La evidencia de este instante no está disponible. Selecciona otro instante expresamente.'});return}
    if(attempt++<3){setCurrent(x=>({...x,key,message:'Recuperando la consulta…'}));timer=setTimeout(request,1000*attempt)}else setCurrent({key,message:'No se pudo completar la consulta de este instante.'});
   }
  };
  if(result){publish(result);if(['queued','preparing','processing'].includes(result.state))timer=setTimeout(request,400)}else{setCurrent({key,message:'Preparando el recorte seleccionado…'});void request()}
  return()=>{c.abort();clearTimeout(timer);clearTimeout(expiryTimer)};
 },[client,job,key]);
 return current.key===key?current:{key,message:''};
}
