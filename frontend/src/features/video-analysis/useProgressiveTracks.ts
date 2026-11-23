import { useEffect, useState } from "react";
import { ClientError, type ApiClient } from "../../services/apiClient";
import type { Playback, Track, TrackPage } from "./progressiveTypes";
export function useProgressiveTracks(
  client: ApiClient,
  state: Playback | undefined,
  active: boolean,
  onUnavailable: () => void,
) {
  const [tracks, setTracks] = useState<Track[]>([]);
  const id = state?.job_id,
    generation = state?.generation,
    revision = state?.enrichment.revision;
  useEffect(() => {
    setTracks([]);
  }, [id, generation]);
  useEffect(() => {
    if (!state || !active) return;
    const c = new AbortController();
    void (async () => {
      let cursor: string | undefined;
      const all: Track[] = [];
      const seen = new Set<string>();
      do {
        const q = new URLSearchParams({ snapshot: String(revision) });
        if (cursor) q.set("cursor", cursor);
        const page = await client.json<TrackPage>(
          "/api/v1/video-jobs/" + id + "/playback/tracks?" + q,
          undefined,
          { signal: c.signal, timeoutMs: 10000, expiresAt: state.expires_at },
        );
        if (
          page.job_id !== id ||
          page.generation !== generation ||
          page.snapshot !== revision ||
          !Array.isArray(page.items) ||
          page.items.length > 100
        )
          throw Error("invalid_tracks");
        for (const t of page.items) {
          if (
            t.job_id !== id ||
            t.generation !== generation ||
            !Number.isSafeInteger(t.track_id) ||
            t.track_id < 1 ||
            !Array.isArray(t.evidence) ||
            t.evidence.length > 21
          )
            throw Error("invalid_track");
          all.push(t);
        }
        cursor = page.next_cursor ?? undefined;
        if (cursor) {
          if (seen.has(cursor) || cursor.length > 512)
            throw Error("invalid_cursor");
          seen.add(cursor);
        }
      } while (cursor && !c.signal.aborted);
      if (!c.signal.aborted) setTracks(all);
    })().catch((e) => {
      if (
        !c.signal.aborted &&
        e instanceof ClientError &&
        [401, 403, 404, 410].includes(e.status)
      )
        onUnavailable();
    });
    return () => c.abort();
  }, [client, id, generation, revision, active]);
  return tracks;
}
