import {useEffect,useState} from 'react';import {ApiClient,ClientError} from '../../services/apiClient';import {parseDetail,type DetectionSummary} from './inspectionContracts';
export function useDetectionSummary(client:ApiClient,id:string,generation:string|undefined,active:boolean,onUnavailable:()=>void){
 const [result,setResult]=useState<DetectionSummary>();
 useEffect(()=>{if(!generation||!active)return;const c=new AbortController();let timer:ReturnType<typeof setTimeout>;
 const poll=async()=>{try{
  const value=parseDetail<DetectionSummary>('DetectionSummary',await client.json('/api/v1/video-jobs/'+id+'/playback/detection-summary?generation='+generation,undefined,{signal:c.signal,timeoutMs:10000}));
  if(c.signal.aborted)return;if(value.job_id!==id||value.generation!==generation||value.total_tracks!==null&&value.classes.reduce((sum,v)=>sum+v.track_count,0)!==value.total_tracks)throw Error('summary_context_mismatch');setResult(value);
  if(!['final','unavailable'].includes(value.status))timer=setTimeout(poll,1000);
 }catch(e){if(c.signal.aborted)return;if(e instanceof ClientError&&[401,403,404,410].includes(e.status)){onUnavailable();return}timer=setTimeout(poll,2000)}};void poll();return()=>{c.abort();clearTimeout(timer)};
 },[client,id,generation,active]);
 return result?.generation===generation?result:undefined;
}
