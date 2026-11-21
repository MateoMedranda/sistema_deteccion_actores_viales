import { useEffect, useState } from "react";
import { ApiClient } from "../services/apiClient";
import { useLegacyJob } from "../hooks/useLegacyJob";
import type { SessionLifecycle } from "../hooks/useSessionLifecycle";
export function EnrichmentPanel({
  client,
  imageId,
  videoId,
  lifecycle,
}: {
  client?: ApiClient;
  imageId?: string;
  videoId?: string;
  lifecycle?: SessionLifecycle;
}) {
  const [results, setResults] = useState<any>();
  const { job, message, setMessage, run, requestOptions, failure } =
    useLegacyJob({
      idKey: "enrichment_job_id",
      lifecycle,
      poll: (id, options) => client!.enrichment(id, options),
      cancel: (id) => client!.cancelEnrichment(id, { timeoutMs: 5000 }),
    });
  useEffect(() => {
    if (job?.status !== "completed" || !client) {
      setResults(undefined);
      return;
    }
    let active = true;
    void client
      .enrichmentResults(job.enrichment_job_id, 1, 50, requestOptions())
      .then((result) => {
        if (active) setResults(result);
      })
      .catch((error) => {
        if (active) failure(error);
      });
    const timer = job.expires_at
      ? setTimeout(
          () => setResults(undefined),
          Math.max(0, Date.parse(job.expires_at) - Date.now()),
        )
      : undefined;
    return () => {
      active = false;
      if (timer) clearTimeout(timer);
    };
  }, [job?.status, job?.enrichment_job_id, client]);
  const start = (kind: "image" | "video", id?: string) => {
    if (!client || !id) return setMessage("No hay una fuente vigente.");
    setResults(undefined);
    void run((options) => client.enrich(kind, id, options));
  };
  return (
    <section>
      <h2>Atributos y placas de video</h2>
      {imageId && (
        <button onClick={() => start("image", imageId)}>
          Enriquecer imagen
        </button>
      )}
      <button onClick={() => start("video", videoId)}>Enriquecer video</button>
      <p role="status">
        {message}{" "}
        {job &&
          "Estado: " + job.status + " · " + (job.progress_percent ?? 0) + "%"}
      </p>
      {results && (
        <pre>{JSON.stringify(results.items ?? results, null, 2)}</pre>
      )}
    </section>
  );
}
