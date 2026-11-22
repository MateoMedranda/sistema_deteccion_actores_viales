import {useEffect,useRef,useState} from "react";
import {ClientError,type ApiClient} from "../../services/apiClient";
import {parseVideoEnrichmentPage,type EnrichmentPage,type VehicleResult} from "../../services/apiTypes";
type Context={identity:string;jobId:string;expiresAt:number;frameCount?:number};
type State={identity?:string;status:"idle"|"loading"|"ready"|"failed"|"expired";page?:EnrichmentPage;selected?:VehicleResult;requestedPage:number};
export function useVideoTrackResults(client?:ApiClient,context?:Context){
 const [state,setState]=useState<State>({status:"idle",requestedPage:1});
 const request=useRef<AbortController>(),version=useRef(0),current=useRef(context);
 current.current=context;
 const load=async(page:number)=>{
  const c=current.current;
  if(!client||!c||!Number.isInteger(page)||page<1)return;
  request.current?.abort();const controller=new AbortController();request.current=controller;const attempt=++version.current;
  if(c.expiresAt<=Date.now()){setState({identity:c.identity,status:"expired",requestedPage:page});return;}
  setState({identity:c.identity,status:"loading",requestedPage:page});
  try{
   if(c.expiresAt<=Date.now()){setState({identity:c.identity,status:"expired",requestedPage:page});return;}
   const raw=await client.enrichmentResults(c.jobId,page,25,{signal:controller.signal,timeoutMs:10000,expiresAt:new Date(c.expiresAt).toISOString()});
   if(controller.signal.aborted||version.current!==attempt||current.current?.identity!==c.identity)return;
   if(c.expiresAt<=Date.now()){setState({identity:c.identity,status:"expired",requestedPage:page});return;}
   const response=parseVideoEnrichmentPage(raw,c.frameCount);
   if(response.page!==page||response.page_size!==25)throw Error("invalid_page");
   setState({identity:c.identity,status:"ready",page:response,requestedPage:page});
  }catch(cause){
   if(controller.signal.aborted||version.current!==attempt||current.current?.identity!==c.identity)return;
   setState({identity:c.identity,status:cause instanceof ClientError&&[401,403,404,410].includes(cause.status)?"expired":"failed",requestedPage:page});
  }
 };
 useEffect(()=>{
  const c=context;setState({identity:c?.identity,status:"idle",requestedPage:1});
  if(!c)return;
  void load(1);let timer:ReturnType<typeof setTimeout>;
  const expire=()=>{const left=c.expiresAt-Date.now();if(left<=0){version.current++;request.current?.abort();setState({identity:c.identity,status:"expired",requestedPage:1});}else timer=setTimeout(expire,Math.min(left,2147483647));};expire();
  return()=>{version.current++;request.current?.abort();clearTimeout(timer);};
 },[client,context?.identity,context?.expiresAt,context?.frameCount]);
 const visible=state.identity===context?.identity?state:{status:"idle" as const,requestedPage:1};
 const select=(track:number)=>setState(old=>old.identity===current.current?.identity?{...old,selected:old.page?.items.find(v=>v.track_id===track)}:old);
 const close=()=>setState(old=>({...old,selected:undefined}));
 return {state:visible,load,select,close};
}
