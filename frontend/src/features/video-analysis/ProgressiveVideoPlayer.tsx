import { useEffect, useRef, useState, type CSSProperties } from "react";
import type { ApiClient } from "../../services/apiClient";
import { ClientError } from "../../services/apiClient";
import type { Frame, Observation } from "./progressiveTypes";
import { clampSeek, terminal } from "./progressiveTypes";
import { classPresentation } from "../image-analysis/classPresentation";
import { useProgressivePlayback } from "./useProgressivePlayback";
import { useProgressiveTracks } from "./useProgressiveTracks";
import {ProgressiveCountTools} from "./ProgressiveCountTools";
import {useProgressiveCount} from "./useProgressiveCount";
import { ProgressiveTrackList, ProgressiveTrackResults } from "./ProgressiveTrackResults";
import { VideoTimeline, clock } from "./VideoTimeline";
import { SourceDecoder } from "./sourceDecoder";
import { playbackDecision } from "./playbackPolicy";
const unsupported =
  "La reproducción progresiva no es compatible con este navegador o formato. Puedes consultar los datos analizados.";
export function ProgressiveVideoPlayer({
  client,
  id,
  active,
  onUnavailable,
}: {
  client: ApiClient;
  id: string;
  active: boolean;
  onUnavailable: () => void;
}) {
  const playback = useProgressivePlayback(client, id, active, onUnavailable),
    { state, latest, cache, ensure } = playback;
  const canvas = useRef<HTMLCanvasElement>(null),
    root = useRef<HTMLDivElement>(null),
    decoder = useRef<SourceDecoder>();
  const forcePaint = useRef(0);
  const wantPlay = useRef(true),
    positionRef = useRef(0),
    running = useRef<{ wall: number; us: number }>(),
    last = useRef<Frame>(),
    selectedRef = useRef<number>(),
    seekVersion = useRef(0);
  const [position, setPosition] = useState(0),
    [phase, setPhase] = useState("Preparando el primer tramo…"),
    [selected, setSelected] = useState<number>(),
    [boxes, setBoxes] = useState<Observation[]>([]);
  const [fullscreen, setFullscreen] = useState(false);
  const [canPlay, setCanPlay] = useState(false);
  const tracks = useProgressiveTracks(client, state, active, playback.retire);
  const [requestMessage,setRequestMessage]=useState("");
  const count=useProgressiveCount(client,id,state,position,active,playback.retire);
  const lineRef=useRef(count.result?.line);lineRef.current=count.result?.line;
  useEffect(()=>{
    if(selected===undefined||!state)return;
    const c=new AbortController();let timer:ReturnType<typeof setTimeout>,attempt=0;
    const request=async()=>{try{setRequestMessage("Consultando el vehículo seleccionado…");await client.json("/api/v1/video-jobs/"+id+"/playback/tracks/"+selected+"/enrich",{method:"POST"},{signal:c.signal,timeoutMs:10000,expiresAt:state.expires_at});if(!c.signal.aborted)setRequestMessage("")}catch(e){if(c.signal.aborted)return;if(e instanceof ClientError&&[401,403,404,410].includes(e.status)){playback.retire();return}setRequestMessage("Recuperando la consulta del vehículo…");timer=setTimeout(request,Math.min(8000,1000*2**attempt++))}};
    void request();return()=>{c.abort();clearTimeout(timer)};
  },[client,id,selected,state?.generation]);
  const pause = () => {
    wantPlay.current = false;
    running.current = undefined;
    setPhase("En pausa");
    setBoxes(last.current?.observations ?? []);
  };
  const select = (id: number) => {
    if (document.fullscreenElement === root.current)
      void document.exitFullscreen();
    pause();
    selectedRef.current = id;
    setSelected(id);
  };
  const seek = async (us: number) => {
    const s = latest.current,
      d = decoder.current;
    if (!s || !d) return;
    const version = ++seekVersion.current,
      target = clampSeek(us, s);
    running.current = undefined;
    count.refresh(target);
    setBoxes([]);
    forcePaint.current++;
    const surface = canvas.current;
    if (surface){
      surface.getContext("2d")?.clearRect(0, 0, surface.width, surface.height);
      delete surface.dataset.frameIndex;delete surface.dataset.timeUs;
    }
    positionRef.current = target;
    setPosition(target);
    setPhase("Preparando el instante seleccionado…");
    await ensure(target);
    const f = cache.current.frame(target);
    if (!f || version !== seekVersion.current) return;
    try {
      await d.seek(f.frame_index);
      if (version === seekVersion.current && !wantPlay.current)
        setPhase("En pausa");
    } catch (e) {
      if (e instanceof ClientError && [401, 403, 404, 410].includes(e.status))
        playback.retire();
      else setPhase(unsupported);
    }
  };
  useEffect(() => {
    const changed = () =>
      setFullscreen(document.fullscreenElement === root.current);
    document.addEventListener("fullscreenchange", changed);
    return () => document.removeEventListener("fullscreenchange", changed);
  }, []);
  useEffect(() => {
    if (!active) {
      wantPlay.current = false;
      running.current = undefined;
      setPhase("En pausa");
    }
  }, [active]);
  useEffect(() => {
    const c = canvas.current,
      s = latest.current;
    if (!c || !s?.source || !active || !state?.media_available) return;
    setCanPlay(false);
    const ctx = c.getContext("2d", { alpha: false });
    if (!ctx || typeof VideoDecoder !== "function") {
      setPhase(unsupported);
      return;
    }
    const abort = new AbortController(),
      d = new SourceDecoder(
        async (start,end)=>{
          let attempt=0;
          while(true){
            try{return await client.sourceRange(id,s.generation,s.source!.size_bytes,start,end,{signal:abort.signal,expiresAt:s.expires_at})}
            catch(e){
              if(abort.signal.aborted||!(e instanceof ClientError)||!([0,408,429].includes(e.status)||e.status>=500))throw e;
              setPhase("Recuperando el video automáticamente…");
              await new Promise<void>((resolve,reject)=>{const stop=()=>{clearTimeout(timer);reject(new DOMException("Aborted","AbortError"))};const timer=setTimeout(()=>{abort.signal.removeEventListener("abort",stop);resolve()},Math.min(8000,1000*2**attempt++));abort.signal.addEventListener("abort",stop,{once:true})});
            }
          }
        },
        s.source.size_bytes,
        abort.signal,
      );
    decoder.current = d;
    let closed = false,
      ready = false,
      failed = false,
      request = 0,
      painted = "";
    const fail = (e: unknown) => {
      if (closed || abort.signal.aborted) return;
      running.current = undefined;
      failed = true;
      setCanPlay(false);
      if (e instanceof ClientError && [401, 403, 404, 410].includes(e.status))
        playback.retire();
      else setPhase(unsupported);
    };
    void d
      .initialize()
      .then(() => {
        if (closed) return;
        const t = d.timeline!,
          rotated = t.rotation === 90 || t.rotation === 270;
        if (
          (rotated ? t.config.codedHeight : t.config.codedWidth) !==
            s.timeline.width ||
          (rotated ? t.config.codedWidth : t.config.codedHeight) !==
            s.timeline.height
        )
          throw Error("orientation_mismatch");
        ready = true;
        setCanPlay(true);
        c.dataset.decoder = "webcodecs";
        return d.fill(0);
      })
      .catch(fail);
    const draw = (f: Frame) => {
      const image = d.frame(f.frame_index);
      if (!image) return false;
      const timeline = d.timeline!,
        sample = timeline.byDisplay[f.frame_index]?.sample;
      if (
        !sample ||
        Math.abs(
          Math.round(
            ((sample.cts - timeline.byDisplay[0].sample.cts) * 1e6) /
              sample.timescale,
          ) - f.start_us,
        ) > 1
      )
        throw Error("timeline_mismatch");
      if (image.timestamp !== f.frame_index * 1000)
        throw Error("frame_identity_mismatch");
      const signature =
        f.frame_index +
        ":" +
        selectedRef.current +
        ":" +
        c.width +
        ":" +
        c.height +
        ":" +
        forcePaint.current+":"+JSON.stringify(lineRef.current);
      if (signature !== painted) {
        const width = s.timeline.width,
          height = s.timeline.height;
        ctx.save();
        ctx.setTransform(c.width / width, 0, 0, c.height / height, 0, 0);
        ctx.fillStyle = "#10203d";
        ctx.fillRect(0, 0, width, height);
        ctx.save();
        const rawW = timeline.config.codedWidth!,
          rawH = timeline.config.codedHeight!;
        if (timeline.rotation === 90) {
          ctx.translate(0, rawW);
          ctx.rotate(-Math.PI / 2);
        } else if (timeline.rotation === 180) {
          ctx.translate(rawW, rawH);
          ctx.rotate(Math.PI);
        } else if (timeline.rotation === 270) {
          ctx.translate(rawH, 0);
          ctx.rotate(Math.PI / 2);
        }
        ctx.drawImage(image, 0, 0, rawW, rawH);
        ctx.restore();
        const scale = Math.max(1, width / 900);
        for (const ob of f.observations) {
          const b = ob.display_bbox;
          if (!b) continue;
          ctx.lineWidth = 5 * scale;
          ctx.strokeStyle = "#10203d";
          ctx.strokeRect(
            b.x_min,
            b.y_min,
            b.x_max - b.x_min,
            b.y_max - b.y_min,
          );
          ctx.lineWidth = 2 * scale;
          ctx.strokeStyle = classPresentation(ob.class_name).color;
          ctx.strokeRect(
            b.x_min,
            b.y_min,
            b.x_max - b.x_min,
            b.y_max - b.y_min,
          );
          if (selectedRef.current === ob.track_id) {
            ctx.lineWidth = 4 * scale;
            ctx.strokeStyle = "#fff";
            ctx.strokeRect(
              b.x_min,
              b.y_min,
              b.x_max - b.x_min,
              b.y_max - b.y_min,
            );
          }
        }
        const line=lineRef.current;
        if(line){ctx.beginPath();ctx.moveTo(line.point_a.x*width,line.point_a.y*height);ctx.lineTo(line.point_b.x*width,line.point_b.y*height);ctx.strokeStyle="#10203d";ctx.lineWidth=7*scale;ctx.stroke();ctx.strokeStyle="#ffd166";ctx.lineWidth=3*scale;ctx.stroke();}
        ctx.restore();
        c.dataset.frameIndex = String(f.frame_index);
        c.dataset.timeUs = String(f.start_us);
        c.dataset.admittedUntilUs = String(latest.current!.available_until_us);
        painted = signature;
      }
      last.current = f;
      d.consume(f.frame_index);
      return true;
    };
    const tick = (now: number) => {
      request = requestAnimationFrame(tick);
      if (closed || failed || !ready || document.hidden) return;
      const current = latest.current;
      if (!current) return;
      if (Date.now() >= Date.parse(current.expires_at)) {
        ctx.clearRect(0, 0, c.width, c.height);
        playback.retire();
        return;
      }
      try {
        if (
          current.timeline.duration_confirmed &&
          current.frames_published !== d.timeline!.byDisplay.length
        )
          throw Error("frame_count_mismatch");
        let target = running.current
          ? running.current.us + (now - running.current.wall) * 1000
          : positionRef.current;
        if (target >= current.available_until_us) {
          target = current.last_frame_start_us ?? 0;
          positionRef.current = target;
          running.current = undefined;
          if(terminal(current))wantPlay.current=false;
          setPhase(
            terminal(current)
              ? "Fin del tramo disponible"
              : "Esperando el siguiente tramo analizado…",
          );
        }
        const f = cache.current.frame(target);
        void ensure(target);
        if (target + 5_000_000 < current.available_until_us)
          void ensure(target + 5_000_000);
        if (f) void d.fill(f.frame_index).catch(fail);
        // Initial admission also waits for the confirmed five-second prefix.
        const initialReady =
          last.current ||
          terminal(current) ||
          current.available_until_us >= current.buffer_seconds * 1e6;
        if (f && initialReady && draw(f)) {
          positionRef.current = target;
          setPosition(f.start_us);
          if (!running.current) setBoxes(f.observations);
          if (
            wantPlay.current &&
            !running.current &&
            playbackDecision(current, target, true, true) === "play"
          ) {
            running.current = { wall: now, us: target };
            setBoxes([]);
            setPhase("Reproduciendo a velocidad original · 1×");
          }
        } else if (running.current) {
          running.current = undefined;
          positionRef.current = last.current?.start_us ?? 0;
          setPhase("Preparando el siguiente cuadro confirmado…");
        }
      } catch (e) {
        fail(e);
      }
    };
    request = requestAnimationFrame(tick);
    const visibility = () => {
      if (document.hidden) pause();
    };
    document.addEventListener("visibilitychange", visibility);
    const session = navigator.mediaSession,
      actions: MediaSessionAction[] = [
        "play",
        "pause",
        "seekto",
        "seekbackward",
        "seekforward",
      ];
    const mediaAction = (event: MediaSessionActionDetails) => {
      if (event.action === "pause") pause();
      else if (event.action === "play") {
        wantPlay.current = true;
        setPhase("Preparando reproducción…");
      } else
        void seek(
          event.action === "seekto"
            ? (event.seekTime ?? 0) * 1e6
            : positionRef.current +
                (event.action === "seekbackward" ? -1 : 1) *
                  (event.seekOffset ?? 5) *
                  1e6,
        );
    };
    for (const action of actions)
      try {
        session?.setActionHandler(action, mediaAction);
      } catch {}
    return () => {
      closed = true;
      abort.abort();
      cancelAnimationFrame(request);
      d.close();
      if (decoder.current === d) decoder.current = undefined;
      running.current = undefined;
      for (const action of actions)
        try {
          session?.setActionHandler(action, null);
        } catch {}
      document.removeEventListener("visibilitychange", visibility);
    };
  }, [client, id, active, state?.media_available, state?.generation, ensure]);
  return (
    <section
      className="progressive-workspace"
      aria-label="Exploración progresiva"
    >
      <div
        ref={root}
        className="progressive-viewer"
        onKeyDown={(e) => {
          if (
            e.key === "Escape" &&
            document.fullscreenElement === root.current
          ) {
            e.preventDefault();
            void document.exitFullscreen();
          }
        }}
      >
        <h3>Escena en análisis</h3>
        <p role="status">
          {playback.message} {phase}
        </p>
        {state?.media_available ? (
          <>
            <div
              className="progressive-surface"
              style={
                {
                  aspectRatio:
                    state.timeline.width + "/" + state.timeline.height,
                  "--video-aspect":
                    state.timeline.width / state.timeline.height,
                } as CSSProperties
              }
            >
              <canvas
                data-job-id={id}
                ref={canvas}
                width={state.timeline.width}
                height={state.timeline.height}
                aria-label={"Video analizado, instante " + clock(position)}
              />
              {count.result?.enabled&&<div className="progressive-count-overlay" aria-label="Contador de cruces" data-count-time-us={count.result.at_us}>
                <span>Cruces · {clock(position)}</span><strong>{count.result.at_us>=0&&count.result.at_us<=position&&position-count.result.at_us<1_000_000?count.result.total:"…"}</strong><small>A → B: {count.result.at_us>=0&&count.result.at_us<=position?count.result.a_to_b:"…"} · B → A: {count.result.at_us>=0&&count.result.at_us<=position?count.result.b_to_a:"…"}</small>
              </div>}
              <div className="progressive-hitboxes">
                {boxes
                  .filter((o) => o.display_bbox)
                  .map((o) => {
                    const b = o.display_bbox!;
                    return (
                      <button
                        key={o.ordinal}
                        aria-label={
                          "Consultar vehículo " +
                          o.track_id +
                          ", " +
                          classPresentation(o.class_name).label
                        }
                        style={{
                          left: (b.x_min / state.timeline.width) * 100 + "%",
                          top: (b.y_min / state.timeline.height) * 100 + "%",
                          width:
                            ((b.x_max - b.x_min) / state.timeline.width) * 100 +
                            "%",
                          height:
                            ((b.y_max - b.y_min) / state.timeline.height) *
                              100 +
                            "%",
                        }}
                        onClick={() => select(o.track_id)}
                      />
                    );
                  })}
              </div>
            </div>
            <div className="progressive-controls">
              <button
                disabled={!canPlay}
                onClick={() => {
                  if(state&&terminal(state)&&positionRef.current>=(state.last_frame_start_us??0))void seek(0);
                  wantPlay.current = true;
                  setPhase("Preparando reproducción…");
                }}
              >
                Reproducir
              </button>
              <button onClick={pause}>Pausar e inspeccionar</button>
              <button
                onClick={() =>
                  void (fullscreen
                    ? document.exitFullscreen()
                    : root.current?.requestFullscreen?.())
                }
              >
                {fullscreen
                  ? "Salir de pantalla completa"
                  : "Pantalla completa"}
              </button>
            </div>
            <VideoTimeline
              disabled={!canPlay}
              state={state}
              position={position}
              onSeek={(us) => void seek(us)}
            />
          </>
        ) : (
          <p>
            {state && terminal(state)
              ? "No hay un tramo reproducible disponible. Puedes consultar los datos conservados o iniciar otro análisis."
              : "El reproductor aparecerá al confirmar los primeros cuadros."}
          </p>
        )}
        {state&&<details className="progressive-vehicles"><summary>Vehículos de este fotograma ({last.current?.observations.length??0})</summary><ProgressiveTrackList observations={last.current?.observations??[]} selected={selected} onSelect={select}/></details>}

      </div>
      <ProgressiveTrackResults
        client={client}
        tracks={tracks}
        selected={selected}
        onSelect={select}
        onUnavailable={playback.retire}
        onClose={()=>{selectedRef.current=undefined;setSelected(undefined);setRequestMessage("")}}
        requestMessage={requestMessage}
      />
      {state?.media_available&&<ProgressiveCountTools source={canvas} pause={pause} enabled={!!count.result?.enabled} onApply={count.configure} onDisable={count.disable} message={count.message} position={clock(position)}/>}
    </section>
  );
}
