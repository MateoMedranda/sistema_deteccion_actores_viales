import {useCallback,useEffect,useRef,useState} from "react";
import {ApiClient} from "../services/apiClient";
import {parseWebSession,type WebSessionReady} from "../services/apiTypes";
type State="connecting"|"ready"|"configuration_missing"|"configuration_invalid"|"upstream_unavailable"|"access_rejected"|"expired";
export function useManagedSession(){
 const [state,setState]=useState<State>("connecting"),[session,setSession]=useState<WebSessionReady>(),[client,setClient]=useState<ApiClient>();
 const pending=useRef<Promise<void>>(),alive=useRef(true),current=useRef<ApiClient>(),revision=useRef(0),attempts=useRef(0);
 const reject=useCallback(()=>{
  try{sessionStorage.removeItem("road-video-011")}catch{}
  revision.current++;current.current=undefined;attempts.current++;
  setClient(undefined);setSession(undefined);setState("access_rejected");
 },[]);
 const connect=useCallback(()=>{
  if(pending.current)return pending.current;
  if(current.current)return Promise.resolve();
  const version=revision.current;setState("connecting");
  const operation=(async()=>{
   try{
    const result=await fetch("/web/session",{method:"POST",headers:{"Content-Type":"application/json","X-UI-Request":"1"},credentials:"same-origin",redirect:"error",body:"{}",signal:AbortSignal.timeout(15000)});
    const response=parseWebSession(await result.json());
    if(!alive.current||version!==revision.current)return;
    if(response.status!=="ready"){attempts.current++;setState(response.status);return;}
    const next=new ApiClient(location.origin+"/web-api","",{csrf:response.csrf_token,expiresAt:Date.parse(response.expires_at),policy:response.policy,onRejected:()=>{if(current.current===next)reject();}});
    current.current=next;attempts.current=0;setClient(next);setSession(response);setState("ready");
   }catch{if(alive.current&&version===revision.current){attempts.current++;setState("upstream_unavailable");}}
  })();
  pending.current=operation;
  void operation.finally(()=>{if(pending.current===operation)pending.current=undefined;});
  return operation;
 },[reject]);
 useEffect(()=>{alive.current=true;void connect();return()=>{alive.current=false;};},[connect]);
 useEffect(()=>{
  if(state==="ready"||state==="connecting")return;
  const delay=Math.min(30000,2000*2**Math.min(4,Math.max(0,attempts.current-1)));
  const timer=setTimeout(()=>void connect(),delay);
  return()=>clearTimeout(timer);
 },[state,connect]);
 useEffect(()=>{
  const recover=()=>{if(!current.current&&document.visibilityState!=="hidden")void connect();};
  window.addEventListener("online",recover);document.addEventListener("visibilitychange",recover);
  return()=>{window.removeEventListener("online",recover);document.removeEventListener("visibilitychange",recover);};
 },[connect]);
 useEffect(()=>{
  if(!session)return;
  const timer=setTimeout(()=>{
   try{sessionStorage.removeItem("road-video-011")}catch{}
   revision.current++;current.current=undefined;setClient(undefined);setSession(undefined);setState("expired");void connect();
  },Math.max(0,Date.parse(session.expires_at)-Date.now()));
  return()=>clearTimeout(timer);
 },[session,connect]);
 const reset=useCallback(async()=>{
  try{sessionStorage.removeItem("road-video-011")}catch{}
  revision.current++;const old=current.current;current.current=undefined;
  setClient(undefined);setSession(undefined);setState("connecting");
  await old?.shutdown();
  try{await fetch("/web/session",{method:"DELETE",headers:{"X-UI-Request":"1","X-UI-CSRF":old?.csrfToken??""},credentials:"same-origin",signal:AbortSignal.timeout(5000)});}catch{}
  if(alive.current)await connect();
 },[connect]);
 return {state,session,client,connect,reset};
}
