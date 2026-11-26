import {useCallback,useEffect,useRef,useState} from 'react';
import {ApiClient,ClientError} from '../../services/apiClient';
import type {Playback} from './progressiveTypes';
import {parseCountLines,lineWrites,sameLines,type Collection,type LineWrite} from './countLinesContracts';
const retryable=(e:unknown)=>e instanceof ClientError?[0,408,429].includes(e.status)||e.status>=500:!(e instanceof Error&&/count_context_mismatch|invalid_count|count_.*invalid/.test(e.message));
export function useCountLines(client:ApiClient,id:string,state:Playback|undefined,active:boolean,onUnavailable:()=>void){
 const [collection,setCollection]=useState<Collection>(),[message,setMessage]=useState(''),[busy,setBusy]=useState(false);
 const ref=useRef({state,active,onUnavailable,collection});ref.current={state,active,onUnavailable,collection};
 const epoch=useRef(0),context=useRef<AbortController>(),write=useRef(false),mutation=useRef(0),reading=useRef<Promise<Collection|undefined>>();
 const identity=useRef(''),retry=useRef<ReturnType<typeof setTimeout>>(),retryAttempt=useRef(0);
 const path='/api/v1/video-jobs/'+id+'/playback/count-lines';
 const accept=useCallback((v:Collection)=>setCollection(old=>old&&old.job_id===v.job_id&&old.generation===v.generation&&old.revision>v.revision?old:v),[]);
 const validate=useCallback((value:unknown,s:Playback)=>{
  const v=parseCountLines<Collection>('Collection',value);
  if(v.job_id!==id||v.generation!==s.generation)throw Error('count_context_mismatch');return v;
 },[id]);
 const read=useCallback(async(signal?:AbortSignal,expected?:Playback)=>{
  const s=expected??ref.current.state;if(!s)return;
  return validate(await client.json(path+'?generation='+s.generation,{}, {signal,expiresAt:s.expires_at}),s);
 },[client,path,validate]);
 const fail=useCallback((e:unknown)=>{
  if(e instanceof ClientError&&[401,403,410].includes(e.status)){context.current?.abort();if(retry.current)clearTimeout(retry.current);ref.current.onUnavailable();return}
  const code=e instanceof ClientError?e.detail.code:'';
  setMessage(e instanceof ClientError&&e.status===404?'Este servicio todavía no admite varias líneas. El video sigue disponible.':code==='count_line_admission_limit'?'Se alcanzó el límite de identidades admitidas. Puedes editar o eliminar líneas existentes.':code==='count_line_limit'?'Se alcanzó el límite de líneas activas. Se conservan las líneas confirmadas.':code==='count_revision_changed'?'Otra pestaña cambió las líneas. Revisa el conflicto; tus borradores se conservan.':'No se pudo confirmar el cambio. Se conserva la configuración recibida del servidor.');
 },[]);
 useEffect(()=>{
  const n=++epoch.current,c=new AbortController();context.current?.abort();context.current=c;mutation.current++;write.current=false;reading.current=undefined;
  if(retry.current)clearTimeout(retry.current);retryAttempt.current=0;
  const key=id+':'+state?.generation;if(identity.current!==key){setCollection(undefined);identity.current=key}setMessage('');setBusy(false);
  if(!state||!active){c.abort();return()=>{if(retry.current)clearTimeout(retry.current);epoch.current++}}
  const s=state;let timer:ReturnType<typeof setTimeout>|undefined,attempt=0;
  const current=()=>!c.signal.aborted&&n===epoch.current;
  const load=async()=>{
   if(!current())return;
   if(write.current||reading.current){timer=setTimeout(()=>void load(),200);return}
   try{const pending=read(c.signal,s);reading.current=pending;const v=await pending;if(current()&&v){accept(v);setMessage('')}}
   catch(e){if(current()){fail(e);if(retryable(e)){setMessage('Recuperando las líneas automáticamente…');timer=setTimeout(()=>void load(),Math.min(8000,200*2**Math.min(attempt++,6)))}}}
   finally{if(current())reading.current=undefined}
  };
  void load();return()=>{c.abort();if(timer)clearTimeout(timer);if(retry.current)clearTimeout(retry.current);epoch.current++;mutation.current++};
 },[state?.generation,active,read,fail]);
 const configure=useCallback(async(lines:LineWrite[])=>{
  if(write.current)throw Error('Hay un cambio pendiente.');const previous=ref.current.collection,s=ref.current.state,n=epoch.current,c=context.current;
  if(!previous||!s||!c||c.signal.aborted||previous.job_id!==id||previous.generation!==s.generation)throw Error('Preparando las líneas…');
  let wanted:LineWrite[];try{wanted=lineWrites(lines)}catch(e){setMessage(e instanceof Error?e.message:'Nombre no válido.');throw e}
  if(new Set(wanted.map(l=>l.name.toLowerCase())).size!==wanted.length||new Set(wanted.map(l=>l.color)).size!==wanted.length){setMessage('Cada línea necesita un nombre y color diferentes.');throw Error('Cada línea necesita un nombre y color diferentes.')}
  const added=wanted.filter(l=>!previous.lines.some(p=>p.line_id===l.line_id)).length;
  if(added&&previous.admitted_count+added>previous.limits.max_admitted_lines){const e=new ClientError(409,{code:'count_line_admission_limit',message:'Se alcanzó el límite de identidades admitidas.'});fail(e);throw e}
  if(sameLines(previous.lines,wanted))return true;
  const token=++mutation.current;write.current=true;setBusy(true);setMessage('Guardando líneas…');
  const current=()=>n===epoch.current&&!c.signal.aborted&&token===mutation.current;
  try{
   let v:Collection;
   try{v=validate(await client.json(path,{method:'PUT',body:JSON.stringify({generation:s.generation,expected_revision:previous.revision,lines:wanted})},{signal:c.signal,expiresAt:s.expires_at}),s)}
   catch(e){if(!current())return false;const confirmed=await read(c.signal,s);if(!current())return false;if(!confirmed||!sameLines(confirmed.lines,wanted)){if(confirmed)accept(confirmed);throw e}v=confirmed}
   if(!current())return false;
   if(v.revision<previous.revision||!sameLines(v.lines,wanted))throw Error('count_context_mismatch');
   accept(v);setMessage('Líneas guardadas. Los conteos se calculan sobre el tramo analizado.');return true;
  }catch(e){if(current())fail(e);throw e}finally{if(token===mutation.current){write.current=false;if(n===epoch.current)setBusy(false)}}
 },[client,id,path,read,fail,validate]);
 const importLegacy=useCallback(async()=>{
  const previous=ref.current.collection,s=ref.current.state,n=epoch.current,c=context.current;
  if(!previous||!s||!c||c.signal.aborted||write.current||previous.job_id!==id||previous.generation!==s.generation)return;
  const token=++mutation.current;write.current=true;setBusy(true);const current=()=>n===epoch.current&&!c.signal.aborted&&token===mutation.current;
  try{
   const v=validate(await client.json(path+'/import-legacy',{method:'POST',body:JSON.stringify({generation:s.generation,expected_revision:previous.revision})},{signal:c.signal,expiresAt:s.expires_at}),s);
   if(v.revision<previous.revision||v.legacy_import.status!=='imported')throw Error('count_context_mismatch');
   if(current()){accept(v);setMessage('Línea anterior importada. Ahora cuenta cruces en ambos sentidos.')}
  }catch(e){if(current()){try{const confirmed=await read(c.signal,s);if(!current())return;if(confirmed&&confirmed.revision>=previous.revision&&confirmed.legacy_import.status==='imported'){accept(confirmed);setMessage('Importación confirmada.')}else fail(e)}catch(error){if(current())fail(error)}}}
  finally{if(token===mutation.current){write.current=false;if(n===epoch.current)setBusy(false)}}
 },[client,id,path,read,fail,validate]);
 const imported=useRef(new Set<string>());
 useEffect(()=>{if(!active||!collection||collection.lines.length||collection.legacy_import.status!=='offered')return;const key=id+collection.generation;if(imported.current.has(key))return;imported.current.add(key);void importLegacy()},[active,collection,importLegacy,id]);
 const reload=useCallback(async function reloadDescriptor():Promise<void>{
  const n=epoch.current,c=context.current;if(!c||c.signal.aborted||write.current||reading.current)return;
  try{const pending=read(c.signal);reading.current=pending;const v=await pending;if(n===epoch.current&&!c.signal.aborted&&v){accept(v);setMessage('');retryAttempt.current=0}}catch(e){if(n===epoch.current&&!c.signal.aborted){fail(e);if(retryable(e)){setMessage('Recuperando las líneas automáticamente…');retry.current=setTimeout(()=>void reloadDescriptor(),Math.min(8000,200*2**Math.min(retryAttempt.current++,6)))}}}finally{if(n===epoch.current)reading.current=undefined}
 },[read,fail]);
 return {collection,message,busy,configure,importLegacy,reload};
}
