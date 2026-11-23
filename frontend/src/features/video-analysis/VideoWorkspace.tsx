import {ProgressiveVideoPlayer} from "./ProgressiveVideoPlayer";
import { MediaUpload } from "../../components/MediaUpload";
import { useEffect, useRef, useState } from "react";
import type { ApiClient } from "../../services/apiClient";
import type { Point } from "../../services/apiTypes";
import { useSessionLifecycle } from "../../hooks/useSessionLifecycle";
import { LineEditor } from "../../components/LineEditor";
import { CountJobPanel } from "../../components/CountJobPanel";
import { VideoProgress } from "./VideoProgress";
import { VideoLegend } from "./VideoLegend";
import { VideoTrackResults } from "./VideoTrackResults";
import { VideoPlayer } from "./VideoPlayer";
import { useVideoAnalysis } from "./useVideoAnalysis";
export function VideoWorkspace({ client, active = true }: { client?: ApiClient; active?: boolean }) {
    const analysis = useVideoAnalysis(client,!!client?.managed), s = analysis.state;
    const root = useRef<HTMLElement>(null), [line, setLine] = useState<[Point, Point]>();
    const [lineVersion, setLineVersion] = useState(0);
    const changeLine = (next?: [Point, Point]) => { setLine(next); setLineVersion(v => v + 1); };
    const lifecycle = useSessionLifecycle(client), policy = client?.policy?.video;
    const ready = s.processing === "ready" && s.video;
    const busy = ["uploading", "checking", "queued", "processing"].includes(s.processing);
    useEffect(() => { setLine(undefined); }, [s.generation]);
    useEffect(() => { if (!active) root.current?.querySelectorAll("video").forEach(video => video.pause()); }, [active]);
    const select = (file?: File) => {
        analysis.choose(file);
        if (file && ((policy && !policy.media_types.includes(file.type)) || (policy && file.size > policy.max_upload_bytes))) analysis.rejectFile("Selecciona un MP4 que respete el tamaño permitido.");
    };
    return (
        <section ref={root} className="video-workspace media-workspace" aria-labelledby="video-heading">
            <div className="workspace-heading">
                <div>
                    <h3 id="video-heading" className="eyebrow">ANÁLISIS DE VIDEO</h3>
                    <p>Analiza una escena, reproduce el resultado y conoce cada vehículo.</p>
                </div><span className="workspace-tag">Video ↗</span></div>
            <MediaUpload kind="video" title="Tu video, una escena completa" description="Vehículos, atributos y placas a lo largo de la escena." inputLabel="Video" selectLabel="Seleccionar video" actionLabel={["failed", "cancelled"].includes(s.processing) ? "Reintentar video" : "Procesar video"} clearLabel="Limpiar video" accept={policy?.media_types.join(",") ?? "video/mp4"} disabled={!client || busy || s.processing === "ready"} file={s.file} generation={s.generation} compact={!!s.video} onChoose={select} onAnalyze={() => void (["failed", "cancelled"].includes(s.processing) ? analysis.retryVideo() : analysis.start())} onReset={() => analysis.choose()}
                hint={<><small>MP4 · Archivos temporales y privados</small><small>{policy ? "Máximo " + new Intl.NumberFormat("es", { maximumFractionDigits: 2 }).format(policy.max_upload_bytes / 1024 / 1024) + " MiB y " + policy.max_duration_seconds + " segundos." : "Preparando los límites de carga automáticamente…"}</small></>} />
            {s.message&&<p role="status" className="video-message">{s.message}</p>}
            <VideoProgress hideEnrichment={!!client?.managed} video={s.video} processingState={s.processing === "idle" ? undefined : s.processing} enrichment={s.enriched} enrichmentState={s.enrichment} />
            <div className="video-stage-actions">{busy && <button onClick={() => void analysis.cancel("processing")}>Cancelar procesamiento</button>}{["submitting", "queued", "processing"].includes(s.enrichment) && <button onClick={() => void analysis.cancel("enrichment")}>Cancelar enriquecimiento</button>}{(s.processing === "interrupted" || s.enrichment === "interrupted") && <button onClick={() => void analysis.resume()}>Reanudar consulta</button>}{["failed", "cancelled", "expired"].includes(s.enrichment) && ready && <button onClick={() => void analysis.retryEnrichment()}>Reintentar enriquecimiento</button>}</div>
            {client?.managed && s.video && <ProgressiveVideoPlayer key={s.generation+":"+s.video.job_id} client={client} id={s.video.job_id} active={active} onUnavailable={analysis.discard}/>}
            {ready && client && <>{!client.managed && <VideoPlayer key={s.generation + ":" + s.video!.job_id} client={client} job={s.video!} active={active} onUnavailable={analysis.discard} />}<VideoLegend classes={s.video!.classes_present} eligible={s.video!.eligible_track_count} />
                {!client.managed&&<details className="video-count-tools"><summary>Conteo por línea</summary><LineEditor key={s.video!.job_id} videoUrl={client.nativeVideo(s.video!.job_id)} dimensions={s.video!.video_metadata ?? undefined} onClear={() => changeLine()} onLine={(a, b) => changeLine([a, b])} /><CountJobPanel key={s.generation + ":" + s.video!.job_id + ":" + lineVersion} client={client} videoId={s.video!.job_id} line={line} lifecycle={lifecycle} /></details>}
                {s.enriched?.status === "completed" && <VideoTrackResults client={client} video={s.video!} job={s.enriched} generation={s.generation} />}
            </>}
        </section>
    );
}
