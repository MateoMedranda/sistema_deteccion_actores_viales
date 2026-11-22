import {VideoLegend} from "./VideoLegend";
import {VideoProgress} from "./VideoProgress";
import {classPresentation} from "../image-analysis/classPresentation";
import type {VideoJob} from "./videoTypes";
import {useEffect,useRef,useState} from "react";
import type {ApiClient} from "../../services/apiClient";
import type {Point} from "../../services/apiTypes";
import {VideoJobPanel} from "../../components/VideoJobPanel";
import {EnrichmentPanel} from "../../components/EnrichmentPanel";
import {LineEditor} from "../../components/LineEditor";
import {CountJobPanel} from "../../components/CountJobPanel";
import {useSessionLifecycle} from "../../hooks/useSessionLifecycle";
export function VideoWorkspace({client,active=true}:{client?:ApiClient;active?:boolean}){
 const root=useRef<HTMLElement>(null),[videoId,setVideoId]=useState<string>(),[preview,setPreview]=useState(""),[line,setLine]=useState<[Point,Point]>();
 const [status,setStatus]=useState<VideoJob>();
 const lifecycle=useSessionLifecycle(client);
 useEffect(()=>{if(!active)root.current?.querySelectorAll("video").forEach(video=>video.pause());},[active]);
 return <section ref={root} className="video-workspace"><p className="eyebrow">ANÁLISIS DE VIDEO</p><h2>El movimiento, en contexto.</h2><p>Procesa una escena vial y explora sus resultados.</p>
 <VideoProgress video={status}/><VideoJobPanel onStatus={setStatus} client={client} onVideo={setVideoId} onPreview={url=>{setPreview(url);setLine(undefined);setVideoId(undefined);}} lifecycle={lifecycle}/>
 {preview&&<LineEditor key={preview} videoUrl={preview} onClear={()=>setLine(undefined)} onLine={(a,b)=>setLine([a,b])}/>}
 {status&&<VideoLegend classes={status.classes_present??null} eligible={status.eligible_track_count??null}/>}
 <CountJobPanel key={"count:"+videoId+":"+JSON.stringify(line)} client={client} videoId={videoId} line={line} lifecycle={lifecycle}/>
 <EnrichmentPanel key={"enrichment:"+videoId} client={client} videoId={videoId} lifecycle={lifecycle}/>
 </section>;
}
