import type {ApiClient} from "../../services/apiClient";
import type {EnrichmentJob} from "../../services/apiTypes";
import type {VideoJob} from "./videoTypes";
import {useVideoTrackResults} from "./useVideoTrackResults";
import {VideoTrackList} from "./VideoTrackList";
import {VideoTrackDetails} from "./VideoTrackDetails";
export function VideoTrackResults({client,video,job,generation}:{client:ApiClient;video:VideoJob;job:EnrichmentJob;generation:number}){
 const results=useVideoTrackResults(client,{identity:generation+":"+video.job_id+":"+job.enrichment_job_id,jobId:job.enrichment_job_id,expiresAt:Math.min(Date.parse(video.expires_at),Date.parse(job.expires_at)),frameCount:video.frame_total_confirmed?video.video_metadata?.frame_count:undefined});
 const {state}=results;
 return <section className="video-results" aria-label="Resultados del enriquecimiento">
 {state.status==="loading"?<p role="status">Cargando trayectorias…</p>:state.status==="failed"?<div role="alert"><p>No pudimos consultar esta página. El video sigue disponible.</p><button onClick={()=>void results.load(state.requestedPage)}>Reintentar página</button></div>:state.status==="expired"?<p role="status">Los resultados han vencido o ya no están disponibles.</p>:state.page?<div className="video-results-grid"><VideoTrackList page={state.page} selected={state.selected?.track_id} onSelect={results.select} onPage={page=>void results.load(page)}/><VideoTrackDetails item={state.selected} metadata={video.frame_total_confirmed?video.video_metadata:null} onClose={results.close}/></div>:null}
 </section>;
}
