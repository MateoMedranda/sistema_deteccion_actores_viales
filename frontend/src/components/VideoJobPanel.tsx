import { useEffect, useRef, useState } from "react";
import { ApiClient } from "../services/apiClient";
import type { SessionLifecycle } from "../hooks/useSessionLifecycle";
import { useLegacyJob } from "../hooks/useLegacyJob";
export function VideoJobPanel({
  client,
  onVideo,
  onPreview,
  lifecycle,
  onStatus,
}: {
  client?: ApiClient;
  onVideo: (id: string) => void;
  onPreview: (url: string) => void;
  lifecycle?: SessionLifecycle;
  onStatus?: (job:any)=>void;
}) {
  const [file, setFile] = useState<File>(),
    [videoUrl, setVideoUrl] = useState(""),
    [inputGeneration, setInputGeneration] = useState(0);
  const urls = useRef(new Set<string>());
  const {
    job,
    message,
    setMessage,
    run,
    alive,
    requestOptions,
    failure,
    invalidate,
  } = useLegacyJob({
    idKey: "job_id",
    onExpired: () => {
      for (const url of urls.current) URL.revokeObjectURL(url);
      urls.current.clear();
      setVideoUrl("");
      setFile(undefined);
      setInputGeneration((g) => g + 1);
      onPreview("");
    },
    lifecycle,
    poll: (id, options) => client!.video(id, options),
    cancel: (id) => client!.cancelVideo(id),
  });
  useEffect(()=>{if(job)onStatus?.(job);},[job,onStatus]);
  useEffect(
    () => () => {
      for (const url of urls.current) URL.revokeObjectURL(url);
      urls.current.clear();
    },
    [],
  );
  useEffect(() => {
    if (job?.status !== "completed" || !client) return;
    let active = true,
      url: string | undefined;
    void client
      .annotatedVideo(job.job_id, requestOptions())
      .then((blob) => {
        if (active && alive.current.alive) {
          url = URL.createObjectURL(blob);
          urls.current.add(url);
          setVideoUrl(url);
        }
      })
      .catch((error) => {
        if (active) failure(error);
      });
    const timer = job.expires_at
      ? setTimeout(
          () => {
            if (url) {
              URL.revokeObjectURL(url);
              urls.current.delete(url);
            }
            setVideoUrl("");
          },
          Math.max(0, Date.parse(job.expires_at) - Date.now()),
        )
      : undefined;
    return () => {
      active = false;
      if (timer) clearTimeout(timer);
      if (url) {
        URL.revokeObjectURL(url);
        urls.current.delete(url);
      }
    };
  }, [job?.status, job?.job_id, client]);
  const choose = (f?: File) => {
    invalidate("");
    setFile(f);
    for (const url of urls.current) URL.revokeObjectURL(url);
    urls.current.clear();
    setVideoUrl("");
    if (f) {
      const url = URL.createObjectURL(f);
      urls.current.add(url);
      onPreview(url);
    }
  };
  const submit = async () => {
    if (!client || !file)
      return setMessage("Configura sesión y selecciona un video.");
    const next = await run((options) => client.uploadVideo(file, options));
    if (next && alive.current.alive) onVideo(next.job_id);
  };
  return (
    <section>
      <h2>Video</h2>
      <input
        key={inputGeneration}
        aria-label="Video"
        disabled={
          !!job &&
          !["completed", "failed", "cancelled", "expired"].includes(job.status)
        }
        type="file"
        accept="video/mp4,video/quicktime"
        onChange={(e) => choose(e.target.files?.[0])}
      />
      <button
        disabled={
          !client ||
          (!!job &&
            !["completed", "failed", "cancelled", "expired"].includes(
              job.status,
            ))
        }
        onClick={() => void submit()}
      >
        Procesar video
      </button>
      <p role="status">
        {message} {job?.status}
      </p>
      {videoUrl && <video className="result-video" controls src={videoUrl} />}
    </section>
  );
}
