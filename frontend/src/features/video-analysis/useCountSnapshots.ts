import {useCallback,useEffect,useRef,useState} from 'react';
import {ApiClient,ClientError} from '../../services/apiClient';
import {parseCountLines,type Collection,type CountSnapshot} from './countLinesContracts';
export function useCountSnapshots(client:ApiClient,id:string,collection:Collection|undefined,position:number,active:boolean,onUnavailable:()=>void,onRevisionChanged?:()=>void){
 const [snapshot,setSnapshot]=useState<CountSnapshot>();const refs=useRef({collection,position,active,onUnavailable,onRevisionChanged});refs.current={collection,position,active,onUnavailable,onRevisionChanged};
 const seq=useRef(0),controller=useRef<AbortController>(),last=useRef(0),pending=useRef(false);
 const request=useCallback(async()=>{
  const {collection:c,position:at,active:a}=refs.current;if(!c||!a||document.hidden||pending.current||performance.now()-last.current<100)return;
  pending.current=true;last.current=performance.now();const n=seq.current,abort=new AbortController();controller.current=abort;
  try{
   const v=parseCountLines<CountSnapshot>('CountSnapshot',await client.json('/api/v1/video-jobs/'+id+'/playback/count-lines/counts?generation='+c.generation+'&revision='+c.revision+'&at_us='+at,{}, {signal:abort.signal,expiresAt:c.expires_at}));
   if(v.job_id!==id||v.generation!==c.generation||v.revision!==c.revision||v.at_us!==at||v.lines.length!==c.lines.length||v.lines.some(l=>!c.lines.some(x=>x.line_id===l.line_id&&x.geometry_revision===l.geometry_revision)))throw Error('count_context_mismatch');
   if(n===seq.current&&!abort.signal.aborted)setSnapshot(v);
  }catch(e){if(!abort.signal.aborted){setSnapshot(undefined);if(e instanceof ClientError&&e.status===409)refs.current.onRevisionChanged?.();if(e instanceof ClientError&&[401,403,410].includes(e.status))refs.current.onUnavailable();}}finally{if(controller.current===abort)pending.current=false}
 },[client,id]);
 const refresh=useCallback((at?:number)=>{seq.current++;controller.current?.abort();pending.current=false;setSnapshot(undefined);if(at!==undefined)refs.current.position=at;void request()},[request]);
 useEffect(()=>{refresh();if(!active)return;const timer=setInterval(()=>void request(),400);return()=>{clearInterval(timer);seq.current++;controller.current?.abort();pending.current=false}},[collection?.generation,collection?.revision,active,request,refresh]);
 useEffect(()=>{if(collection?.lines.length&&(!snapshot||snapshot.lines.some(l=>l.status==='ready'&&(position<snapshot.at_us||position>=l.valid_until_us))))void request()},[position,collection?.revision,snapshot,request]);
 return {snapshot,refresh};
}
