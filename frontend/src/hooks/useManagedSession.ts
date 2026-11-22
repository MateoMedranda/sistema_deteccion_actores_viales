import {useCallback,useEffect,useRef,useState} from "react";
import {ApiClient} from "../services/apiClient";
import {parseWebSession,type WebSessionReady} from "../services/apiTypes";
type State="connecting"|"ready"|"configuration_missing"|"configuration_invalid"|"upstream_unavailable"|"access_rejected"|"expired";
export function useManagedSession(){
 const [state,setState]=useState<State>("connecting"),[session,setSession]=useState<WebSessionReady>(),[client,setClient]=useState<ApiClient>();
 const promise=useRef<Promise<unknown>>(),alive=useRef(true),current=useRef<ApiClient>();
 const reject=useCallback(()=>{setClient(undefined);setSession(undefined);setState("access_rejected");},[]);
 const connect=useCallback(async()=>{
  setState("connecting");
  if(!promise.current)promise.current=fetch("/web/session",{method:"POST",headers:{"Content-Type":"application/json","X-UI-Request":"1"},credentials:"same-origin",redirect:"error",body:"{}",signal:AbortSignal.timeout(15000)}).then(r=>r.json()).finally(()=>{promise.current=undefined;});
  try{
   const response=parseWebSession(await promise.current);
   if(!alive.current)return;
   if(response.status!=="ready"){setState(response.status);return;}
   const next=new ApiClient(location.origin+"/web-api","",{csrf:response.csrf_token,expiresAt:Date.parse(response.expires_at),onRejected:reject});
   current.current=next;setClient(next);setSession(response);setState("ready");
  }catch{if(alive.current)setState("upstream_unavailable");}
 },[reject]);
 useEffect(()=>{alive.current=true;void connect();return()=>{alive.current=false;};},[connect]);
 useEffect(()=>{
  if(!session)return;
  const timer=setTimeout(()=>{setClient(undefined);setSession(undefined);setState("expired");},Math.max(0,Date.parse(session.expires_at)-Date.now()));
  return()=>clearTimeout(timer);
 },[session]);
 const reset=useCallback(async()=>{
  const old=current.current;current.current=undefined;
  setClient(undefined);setSession(undefined);setState("connecting");
  await old?.shutdown();
  try{await fetch("/web/session",{method:"DELETE",headers:{"X-UI-Request":"1","X-UI-CSRF":old?.csrfToken??""},credentials:"same-origin",signal:AbortSignal.timeout(5000)});}catch{}
  if(alive.current)await connect();
 },[connect]);
 return {state,session,client,connect,reset};
}
