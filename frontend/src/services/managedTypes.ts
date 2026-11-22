import {parseImagePolicy,type ImagePolicy} from "./apiTypes";
export type WebPolicy={image:ImagePolicy;video:{media_types:string[];max_upload_bytes:number;max_duration_seconds:number;max_width:number;max_height:number;max_fps:number;max_frames:number};capabilities:{image_detection:boolean;video_analysis:boolean;attributes:boolean;plates:boolean}};
export type WebSessionReady={status:"ready";epoch:string;expires_at:string;csrf_token:string;policy:WebPolicy};
export type WebSessionError={status:"configuration_missing"|"configuration_invalid"|"upstream_unavailable"|"access_rejected"};
export function parseWebSession(value:unknown):WebSessionReady|WebSessionError{
 if(!value||typeof value!=="object")throw new Error("invalid_session");
 const r=value as Record<string,any>;
 if(r.status!=="ready"){
  if(!["configuration_missing","configuration_invalid","upstream_unavailable","access_rejected"].includes(r.status))throw new Error("invalid_session");
  return {status:r.status};
 }
 if(!/^[0-9a-f-]{36}$/i.test(r.epoch)||!/[Z]$|\+00:00$/.test(r.expires_at)||!Number.isFinite(Date.parse(r.expires_at))||Date.parse(r.expires_at)<=Date.now()||!/^[A-Za-z0-9_-]{43}$/.test(r.csrf_token))throw new Error("invalid_session");
 const image=parseImagePolicy(r.policy?.image),v=r.policy?.video,c=r.policy?.capabilities;
 if(!v||!c||!Array.isArray(v.media_types)||!v.media_types.length||v.media_types.some((x:unknown)=>!["video/mp4","video/quicktime"].includes(String(x))))throw new Error("invalid_policy");
 for(const k of ["max_upload_bytes","max_duration_seconds","max_width","max_height","max_fps","max_frames"])if(typeof v[k]!=="number"||!Number.isFinite(v[k])||v[k]<=0)throw new Error("invalid_policy");
 for(const k of ["image_detection","video_analysis","attributes","plates"])if(typeof c[k]!=="boolean")throw new Error("invalid_policy");
 return {status:"ready",epoch:r.epoch,expires_at:r.expires_at,csrf_token:r.csrf_token,policy:{image,video:v,capabilities:c}};
}
