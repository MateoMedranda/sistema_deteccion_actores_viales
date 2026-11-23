import { useCallback, useEffect, useRef, useState } from "react";
import { ApiClient, ClientError } from "../../services/apiClient";
import { FrameCache } from "./frameCache";
import { parsePlayback, type Playback } from "./progressiveTypes";
export function useProgressivePlayback(
  client: ApiClient,
  id: string,
  active: boolean,
  onUnavailable: () => void,
) {
  const [state, setState] = useState<Playback>(),
    [message, setMessage] = useState("Preparando el primer tramo analizado…");
  const latest = useRef<Playback>(),
    cache = useRef(new FrameCache()),
    pending = useRef(new Map<number, Promise<void>>());
  const controller = useRef(new AbortController()),
    notify = useRef(onUnavailable);
  notify.current = onUnavailable;
  const retire = useCallback(() => {
    controller.current.abort();
    latest.current = undefined;
    cache.current.clear();
    setState(undefined);
    setMessage("El resultado ya no está disponible.");
    notify.current();
  }, []);
  useEffect(() => {
    const c = new AbortController();
    controller.current = c;
    cache.current.clear();
    pending.current.clear();
    latest.current = undefined;
    let timer: ReturnType<typeof setTimeout>,
      failures = 0;
    const poll = async () => {
      if (c.signal.aborted) return;
      if (!active || document.hidden) {
        timer = setTimeout(poll, 500);
        return;
      }
      try {
        const s = parsePlayback(
          await client.json(
            "/api/v1/video-jobs/" + id + "/playback",
            undefined,
            { signal: c.signal, timeoutMs: 10000 },
          ),
          id,
        );
        if (c.signal.aborted) return;
        if (Date.parse(s.expires_at) <= Date.now()) {
          retire();
          return;
        }
        if (
          latest.current &&
          (s.generation !== latest.current.generation ||
            s.revision < latest.current.revision)
        )
          throw Error("stale_playback");
        latest.current = s;
        setState(s);
        failures = 0;
        setMessage(
          s.analysis_state === "partial_failed"
            ? "El análisis se interrumpió. Puedes explorar el tramo confirmado."
            : s.analysis_state === "complete"
              ? "Análisis completo."
              : "El video continúa analizándose.",
        );
      } catch (e) {
        if (c.signal.aborted) return;
        if (
          e instanceof ClientError &&
          [401, 403, 404, 410].includes(e.status)
        ) {
          retire();
          return;
        }
        failures++;
        setMessage(
          "Reconectando automáticamente. Se conserva el tramo confirmado.",
        );
      }
      timer = setTimeout(
        poll,
        failures ? Math.min(8000, 1000 * 2 ** (failures - 1)) : 500,
      );
    };
    void poll();
    return () => {
      c.abort();
      clearTimeout(timer);
      cache.current.clear();
      pending.current.clear();
    };
  }, [client, id, active, retire]);
  useEffect(() => {
    if (!state) return;
    const timer = setTimeout(
      retire,
      Math.max(
        0,
        Math.min(2147483647, Date.parse(state.expires_at) - Date.now()),
      ),
    );
    return () => clearTimeout(timer);
  }, [state?.expires_at, retire]);
  const ensure = useCallback(
    async (us: number) => {
      const s = latest.current,
        c = controller.current;
      if (!s || c.signal.aborted || us >= s.available_until_us) return;
      const start = Math.floor(Math.max(0, us) / 5_000_000) * 5_000_000,
        end = Math.min(start + 5_000_000, s.available_until_us);
      if (cache.current.covers(start, end)) return;
      if (pending.current.has(start)) return pending.current.get(start);
      if (pending.current.size >= 4) return;
      const operation = cache.current
        .load(
          s,
          start,
          end,
          (cursor) => {
            const q = new URLSearchParams({
              from_us: String(start),
              to_us: String(end),
              snapshot: String(s.revision),
            });
            if (cursor) q.set("cursor", cursor);
            return client.json(
              "/api/v1/video-jobs/" + id + "/playback/frames?" + q,
              undefined,
              { signal: c.signal, timeoutMs: 10000, expiresAt: s.expires_at },
            );
          },
          c.signal,
        )
        .catch((e) => {
          if (
            e instanceof ClientError &&
            [401, 403, 404, 410].includes(e.status)
          )
            retire();
          if (!c.signal.aborted)
            setMessage("Preparando las anotaciones del tramo…");
        })
        .finally(() => pending.current.delete(start));
      pending.current.set(start, operation);
      return operation;
    },
    [client, id, retire],
  );
  return { state, latest, cache, ensure, message, retire };
}
