import {useCallback,useEffect,useRef,useState} from 'react';
import {ApiClient,ClientError} from '../../services/apiClient';
import type {Playback} from './progressiveTypes';
import {parseCountLines,lineWrites,sameLines,type Collection,type CountSnapshot,type LineWrite} from './countLinesContracts';
export function useCountLines(client:ApiClient,id:string,state:Playback|undefined,active:boolean,onUnavailable:()=>void){
 const [collection,setCollection]=useState<Collection>(),[message,setMessage]=useState(''),[busy,setBusy]=useState(false);
 const ref=useRef({state,active,onUnavailable,collection});ref.current={state,active,onUnavailable,collection};
 const epoch=useRef(0),abort=useRef<AbortController>(),write=useRef(false);
 const path='/api/v1/video-jobs/'+id+'/playback/count-lines';
 const read=useCallback(async(signal?:AbortSignal)=>{
  const s=ref.current.state;if(!s)return;
  const v=parseCountLines<Collection>('Collection',await client.json(path+'?generation='+s.generation,{}, {signal,expiresAt:s.expires_at}));
  if(v.job_id!==id||v.generation!==s.generation)throw Error('count_context_mismatch');return v;
 },[client,id,path]);
 const fail=useCallback((e:unknown)=>{if(e instanceof ClientError&&[401,403,410].includes(e.status))ref.current.onUnavailable();else setMessage(e instanceof ClientError&&e.status===404?'Este servicio todavía no admite varias líneas. El video sigue disponible.':'No se pudo confirmar el cambio. Se conserva la configuración recibida del servidor.');},[]);
 useEffect(()=>{
  const n=++epoch.current;abort.current?.abort();setCollection(undefined);setMessage('');
  if(!state||!active)return;const c=new AbortController();abort.current=c;
  void read(c.signal).then(v=>{if(!c.signal.aborted&&n===epoch.current)setCollection(v)}).catch(e=>{if(!c.signal.aborted)fail(e)});
  return()=>{c.abort();epoch.current++};
 },[state?.generation,active,read,fail]);
 const configure=useCallback(async(lines:LineWrite[])=>{
  if(write.current)throw Error('Hay un cambio pendiente.');const previous=ref.current.collection,s=ref.current.state,n=epoch.current;
  if(!previous||!s)throw Error('Preparando las líneas…');
  let wanted:LineWrite[];try{wanted=lineWrites(lines)}catch(e){setMessage(e instanceof Error?e.message:"Nombre no válido.");throw e}
  if(new Set(wanted.map(l=>l.name.toLocaleLowerCase())).size!==wanted.length||new Set(wanted.map(l=>l.color)).size!==wanted.length){setMessage('Cada línea necesita un nombre y color diferentes.');throw Error('Cada línea necesita un nombre y color diferentes.');}
  if(sameLines(previous.lines,wanted))return true;
  write.current=true;setBusy(true);setMessage('Guardando líneas…');
  const c=new AbortController();abort.current?.abort();abort.current=c;
  try{
   let v:Collection;
   try{v=parseCountLines<Collection>('Collection',await client.json(path,{method:'PUT',body:JSON.stringify({generation:s.generation,expected_revision:previous.revision,lines:wanted})},{signal:c.signal,expiresAt:s.expires_at}));}
   catch(e){const confirmed=await read(c.signal);if(!confirmed||!sameLines(confirmed.lines,wanted)){if(confirmed&&n===epoch.current)setCollection(confirmed);throw e}v=confirmed;}
   if(n!==epoch.current||c.signal.aborted)return false;
   if(v.job_id!==id||v.generation!==s.generation||!sameLines(v.lines,wanted))throw Error('count_context_mismatch');
   setCollection(v);setMessage('Líneas guardadas. Los conteos se calculan sobre el tramo analizado.');return true;
  }catch(e){if(!c.signal.aborted)fail(e);throw e}finally{write.current=false;if(n===epoch.current)setBusy(false)}
 },[client,id,path,read,fail]);
 const importLegacy=useCallback(async()=>{
  const previous=ref.current.collection,s=ref.current.state,n=epoch.current;if(!previous||!s||write.current)return;
  write.current=true;setBusy(true);const c=new AbortController();abort.current?.abort();abort.current=c;
  try{const v=parseCountLines<Collection>('Collection',await client.json(path+'/import-legacy',{method:'POST',body:JSON.stringify({generation:s.generation,expected_revision:previous.revision})},{signal:c.signal,expiresAt:s.expires_at}));if(n===epoch.current&&!c.signal.aborted){setCollection(v);setMessage('Línea anterior importada. Ahora cuenta cruces en ambos sentidos.')}}catch(e){if(!c.signal.aborted){try{const confirmed=await read(c.signal);if(confirmed&&n===epoch.current&&confirmed.legacy_import.status==='imported'){setCollection(confirmed);setMessage('Importación confirmada.')}else fail(e)}catch{fail(e)}}}finally{write.current=false;if(n===epoch.current)setBusy(false)}
 },[client,path,read,fail]);
 const imported=useRef(new Set<string>());
 useEffect(()=>{if(!active||!collection||collection.lines.length||collection.legacy_import.status!=='offered')return;const key=id+collection.generation;if(imported.current.has(key))return;imported.current.add(key);void importLegacy()},[active,collection,importLegacy,id]);
 const reload=useCallback(async()=>{const n=epoch.current;try{const v=await read(abort.current?.signal);if(n===epoch.current&&v)setCollection(v)}catch(e){fail(e)}},[read,fail]);
 return {collection,message,busy,configure,importLegacy,reload};
}
