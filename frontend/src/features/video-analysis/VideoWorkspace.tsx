import {useEffect,useRef,useState} from "react";
import type {ApiClient} from "../../services/apiClient";
import type {Point} from "../../services/apiTypes";
import {useSessionLifecycle} from "../../hooks/useSessionLifecycle";
import {LineEditor} from "../../components/LineEditor";
import {CountJobPanel} from "../../components/CountJobPanel";
import {VideoProgress} from "./VideoProgress";
import {VideoLegend} from "./VideoLegend";
import {VideoPlayer} from "./VideoPlayer";
import {useVideoAnalysis} from "./useVideoAnalysis";
export function VideoWorkspace({client,active=true}:{client?:ApiClient;active?:boolean}){
 const analysis=useVideoAnalysis(client),s=analysis.state;
 const root=useRef<HTMLElement>(null),[line,setLine]=useState<[Point,Point]>();
 const lifecycle=useSessionLifecycle(client),policy=client?.policy?.video;
 const ready=s.processing==="ready"&&s.video;
 const busy=["uploading","checking","queued","processing"].includes(s.processing);
 useEffect(()=>{setLine(undefined);},[s.generation]);
 useEffect(()=>{if(!active)root.current?.querySelectorAll("video").forEach(video=>video.pause());},[active]);
 const select=(file?:File)=>{
  analysis.choose(file);
  if(file&&((policy&&!policy.media_types.includes(file.type))||(policy&&file.size>policy.max_upload_bytes)))analysis.rejectFile("Selecciona un MP4 que respete el tamaño permitido.");
 };
 return <section ref={root} className="video-workspace" aria-labelledby="video-heading">
 <div className="workspace-intro"><p className="eyebrow">ANÁLISIS DE VIDEO</p><h2 id="video-heading">El movimiento, en contexto.</h2><p>Analiza una escena, reproduce el resultado y conoce cada vehículo.</p></div>
 <section className="video-upload-card" aria-label="Carga de video"><div className="upload-symbol" aria-hidden="true">↑</div><div><h3>Tu video, una escena completa</h3><p>Contornos claros y consulta automática de atributos y placas.</p><label className="file-picker">Seleccionar video<input key={s.generation} aria-label="Video" type="file" accept={policy?.media_types.join(",")??"video/mp4"} onChange={e=>select(e.target.files?.[0])}/></label><p className="muted">{policy?"MP4 · hasta "+Math.round(policy.max_upload_bytes/1024/1024)+" MB · "+policy.max_duration_seconds+" segundos":"MP4 · evidencia temporal y privada"}</p></div>
 <div className="upload-actions"><p>{s.file?.name??"Ningún archivo seleccionado"}</p><button className="primary" disabled={!client||!s.file||busy||s.processing==="ready"} onClick={()=>void (["failed","cancelled"].includes(s.processing)?analysis.retryVideo():analysis.start())}>{["failed","cancelled"].includes(s.processing)?"Reintentar video":"Procesar video"}</button></div></section>
 <p role="status" className="video-message">{s.message}</p>
 <VideoProgress video={s.video} processingState={s.processing==="idle"?undefined:s.processing} enrichment={s.enriched} enrichmentState={s.enrichment}/>
 <div className="video-stage-actions">{busy&&<button onClick={()=>void analysis.cancel("processing")}>Cancelar procesamiento</button>}{["submitting","queued","processing"].includes(s.enrichment)&&<button onClick={()=>void analysis.cancel("enrichment")}>Cancelar enriquecimiento</button>}{(s.processing==="interrupted"||s.enrichment==="interrupted")&&<button onClick={()=>void analysis.resume()}>Reanudar consulta</button>}{["failed","cancelled","expired"].includes(s.enrichment)&&ready&&<button onClick={()=>void analysis.retryEnrichment()}>Reintentar enriquecimiento</button>}</div>
 {ready&&client&&<><VideoPlayer key={s.generation+":"+s.video!.job_id} client={client} job={s.video!} active={active} onUnavailable={analysis.discard}/><VideoLegend classes={s.video!.classes_present} eligible={s.video!.eligible_track_count}/>
 <details className="video-count-tools"><summary>Conteo por línea</summary><LineEditor key={s.video!.job_id} videoUrl={client.nativeVideo(s.video!.job_id)} onClear={()=>setLine(undefined)} onLine={(a,b)=>setLine([a,b])}/><CountJobPanel key={s.generation+":"+s.video!.job_id+":"+JSON.stringify(line)} client={client} videoId={s.video!.job_id} line={line} lifecycle={lifecycle}/></details>
 {s.enriched?.status==="completed"&&<section className="video-result-summary"><h3>Vehículos analizados</h3><p>{s.enriched.results_ready} resultados disponibles.</p></section>}
 </>}
 </section>;
}
