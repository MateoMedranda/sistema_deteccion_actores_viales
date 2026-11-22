export type ProcessingPhase="queued"|"frames"|"encoding"|"publishing"|"ready"|"failed"|"cancelled";
export type VideoMetadata={width:number;height:number;fps:number;frame_count:number;duration_seconds:number;timebase:"processed-cfr"};
export type VideoJob={job_id:string;status:"queued"|"processing"|"completed"|"failed"|"cancelled";progress_percent:number;processed_frames:number;total_frames:number;expires_at:string;processing_phase:ProcessingPhase|null;frame_total_confirmed:boolean;video_metadata:VideoMetadata|null;eligible_track_count:number|null;classes_present:string[]|null};
export function parseVideoJob(value:unknown):VideoJob{
 if(!value||typeof value!=="object")throw Error("invalid_video");
 const v=value as Record<string,any>,phases:ProcessingPhase[]=["queued","frames","encoding","publishing","ready","failed","cancelled"];
 if(typeof v.job_id!=="string"||!v.job_id||v.job_id.length>128||!["queued","processing","completed","failed","cancelled"].includes(v.status)||!Number.isFinite(Date.parse(v.expires_at)))throw Error("invalid_video");
 for(const k of ["processed_frames","total_frames"])if(!Number.isInteger(v[k])||v[k]<0)throw Error("invalid_video");
 if(typeof v.progress_percent!=="number"||v.progress_percent<0||v.progress_percent>100)throw Error("invalid_video");
 if(v.frame_total_confirmed!==undefined&&typeof v.frame_total_confirmed!=="boolean")throw Error("invalid_video");
 const phase=v.processing_phase??null;
 if(phase!==null&&!phases.includes(phase))throw Error("invalid_phase");
 if(phase!==null&&v.status!==(["frames","encoding","publishing"].includes(phase)?"processing":phase==="ready"?"completed":phase))throw Error("invalid_phase");
 const metadata=v.video_metadata??null,eligible=v.eligible_track_count??null,classes=v.classes_present??null;
 if(eligible!==null&&(!Number.isInteger(eligible)||eligible<0))throw Error("invalid_video");
 if(classes!==null&&(!Array.isArray(classes)||classes.some((c:unknown)=>typeof c!=="string"||!c||c.length>128)||new Set(classes).size!==classes.length))throw Error("invalid_video");
 if(metadata){
  for(const k of ["width","height","frame_count"])if(!Number.isInteger(metadata[k])||metadata[k]<=0)throw Error("invalid_metadata");
  if(!Number.isFinite(metadata.fps)||metadata.fps<=0||!Number.isFinite(metadata.duration_seconds)||Math.abs(metadata.frame_count/metadata.fps-metadata.duration_seconds)>1e-5||metadata.timebase!=="processed-cfr")throw Error("invalid_metadata");
 }
 if(phase==="ready"&&(!metadata||v.frame_total_confirmed!==true||eligible===null||classes===null))throw Error("invalid_ready");
 return {job_id:v.job_id,status:v.status,progress_percent:v.progress_percent,processed_frames:v.processed_frames,total_frames:v.total_frames,expires_at:v.expires_at,processing_phase:phase,frame_total_confirmed:v.frame_total_confirmed===true,video_metadata:metadata,eligible_track_count:eligible,classes_present:classes};
}
