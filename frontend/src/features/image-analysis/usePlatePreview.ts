import {useEffect,useRef,useState} from "react";
import {ApiClient,ClientError} from "../../services/apiClient";
import type {PlatePreviewContext,PlatePreviewMetadata} from "../../services/apiTypes";
type PreviewState={key:string;status:"idle"|"preparing"|"available"|"not_applicable"|"failed"|"expired";url?:string;metadata?:PlatePreviewMetadata;errorCode?:string};
export function usePlatePreview(client?:ApiClient,context?:PlatePreviewContext,onRejected?:(error:unknown)=>void){
 const key=context?JSON.stringify(context):"",rejected=useRef(onRejected);rejected.current=onRejected;
 const [state,setState]=useState<PreviewState>({key:"",status:"idle"}),[attempt,retry]=useState(0);
 const [mode,setMode]=useState<{key:string;view:"original"|"processed";zoom:1|2|4}>({key:"",view:"original",zoom:1});
 useEffect(()=>{
  if(!client||!context){setState({key,status:"idle"});return;}
  const controller=new AbortController();let url:string|undefined,timer:ReturnType<typeof setTimeout>|undefined;
  setState({key,status:"preparing"});
  const retire=()=>{controller.abort();if(url){URL.revokeObjectURL(url);url=undefined;}};
  timer=setTimeout(()=>{retire();setState({key,status:"expired"});},Math.max(0,context.expiresAt-Date.now()));
  void client.platePreview(context,{signal:controller.signal,deadline:performance.now()+10000,expiresAt:context.expiresAt}).then(value=>{
   if(controller.signal.aborted)return;
   if(Date.parse(value.metadata.expires_at)<=Date.now()){retire();setState({key,status:"expired"});return;}
   url=URL.createObjectURL(value.blob);
   setState({key,status:"available",url,metadata:value.metadata});
   clearTimeout(timer);
   timer=setTimeout(()=>{retire();setState({key,status:"expired"});},Math.max(0,Date.parse(value.metadata.expires_at)-Date.now()));
  }).catch(error=>{
   if(controller.signal.aborted)return;
   if(error instanceof ClientError&&[401,404,410].includes(error.status)){retire();setState({key,status:"expired"});rejected.current?.(error);return;}
   setState({key,status:error instanceof ClientError&&error.status===422?"not_applicable":"failed",errorCode:error instanceof ClientError?error.detail.code:"invalid_response"});
  });
  return ()=>{clearTimeout(timer);retire();};
 },[client,key,attempt]);
 const visible=state.key===key?state:{key,status:"idle" as const};
 return {...visible,view:mode.key===key?mode.view:"original" as const,zoom:mode.key===key?mode.zoom:1 as const,
  setView:(view:"original"|"processed")=>setMode(m=>({key,zoom:m.key===key?m.zoom:1,view})),
  setZoom:(zoom:1|2|4)=>setMode(m=>({key,view:m.key===key?m.view:"original",zoom})),
  retry:()=>{setMode({key,view:"original",zoom:1});retry(n=>n+1);}};
}
