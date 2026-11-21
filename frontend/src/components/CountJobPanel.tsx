import type { Point } from "../services/apiTypes";
import { ApiClient } from "../services/apiClient";
import { useLegacyJob } from "../hooks/useLegacyJob";
import type { SessionLifecycle } from "../hooks/useSessionLifecycle";
export function CountJobPanel({
  client,
  videoId,
  line,
  lifecycle,
}: {
  client?: ApiClient;
  videoId?: string;
  line?: [Point, Point];
  lifecycle?: SessionLifecycle;
}) {
  const { job, message, setMessage, run } = useLegacyJob({
    idKey: "count_job_id",
    lifecycle,
    poll: (id, options) => client!.countJob(id, options),
    cancel: (id) => client!.cancelCount(id),
  });
  const start = () => {
    if (!client || !videoId || !line)
      return setMessage("Completa video y línea primero.");
    void run((options) => client.count(videoId, ...line, options));
  };
  return (
    <section>
      <h2>Conteo</h2>
      <button onClick={start}>Iniciar conteo</button>
      <p role="status">
        {message}{" "}
        {job &&
          "Estado: " + job.status + " · " + (job.progress_percent ?? 0) + "%"}
      </p>
      {job?.summary?.length > 0 && (
        <pre>{JSON.stringify(job.summary, null, 2)}</pre>
      )}
      {job?.events?.length > 0 && (
        <pre>{JSON.stringify(job.events, null, 2)}</pre>
      )}
    </section>
  );
}
