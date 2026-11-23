export type Box = {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
};
export type Observation = {
  ordinal: number;
  track_id: number;
  class_id: number;
  class_name: string;
  confidence: number;
  raw_bbox: Box;
  display_bbox: Box | null;
};
export type Frame = {
  frame_index: number;
  start_us: number;
  end_us: number;
  pts: string;
  observation_offset: number;
  observation_total: number;
  observations: Observation[];
};
export type Playback = {
  job_id: string;
  generation: string;
  revision: number;
  analysis_state: "queued" | "analyzing" | "complete" | "partial_failed";
  export_state: string;
  frames_processed: number;
  frames_published: number;
  available_until_us: number;
  last_frame_start_us: number | null;
  media_available: boolean;
  source: { url: string; media_type: "video/mp4"; size_bytes: number } | null;
  timeline: {
    timebase: "source-pts";
    width: number;
    height: number;
    display_width: number;
    display_height: number;
    pixel_to_display: number[];
    duration_us: number | null;
    duration_confirmed: boolean;
    playback_offset_us: number;
  };
  buffer_seconds: number;
  expires_at: string;
  error_code: string | null;
  enrichment: {
    revision: number;
    status: string;
    source_closed: boolean;
    discovered_units: number;
    provisional_ready_units: number;
    terminal_units: number;
    total_units: number | null;
  };
};
export type FramePage = {
  job_id: string;
  generation: string;
  snapshot: number;
  from_us: number;
  to_us: number;
  frames: Frame[];
  next_cursor: string | null;
};
export type Evidence = {
  evidence_id: string;
  frame_index: number;
  time_us: number;
  vehicle_bbox: Box;
  provisional: boolean;
  vehicle_url: string | null;
  plate_url: string | null;
  expires_at: string;
};
export type Track = {
  job_id: string;
  generation: string;
  unit_id: string;
  track_id: number;
  discovery_ordinal: number;
  class_name: string;
  first_seen_us: number;
  last_seen_us: number;
  state: string;
  final: boolean;
  result_revision: number;
  evidence_revision: number;
  attributes: {
    status: string;
    items: {
      name: string;
      value: string;
      confidence: number;
      evidence_id: string;
    }[];
    error_code: string | null;
  };
  plate: {
    status: string;
    text: string | null;
    ocr_confidence: number | null;
    used_enhancement: boolean;
    policy_id: string;
    evidence_ids: string[];
    error_code: string | null;
  };
  evidence: Evidence[];
  expires_at: string;
};
export type TrackPage = {
  job_id: string;
  generation: string;
  snapshot: number;
  items: Track[];
  next_cursor: string | null;
};
const uint = (n: unknown): n is number =>
  Number.isSafeInteger(n) && Number(n) >= 0;
const record = (v: unknown): Record<string, any> => {
  if (!v || typeof v !== "object" || Array.isArray(v))
    throw Error("invalid_response");
  return v as Record<string, any>;
};
export function parsePlayback(value: unknown, id: string): Playback {
  const v = record(value);
  if (
    v.job_id !== id ||
    typeof v.generation !== "string" ||
    !uint(v.revision) ||
    !uint(v.available_until_us) ||
    !uint(v.frames_published) ||
    !["queued", "analyzing", "complete", "partial_failed"].includes(
      v.analysis_state,
    ) ||
    !Number.isFinite(Date.parse(v.expires_at)) ||
    !(v.buffer_seconds > 0 && v.buffer_seconds <= 30)
  )
    throw Error("invalid_playback");
  const t = record(v.timeline),
    e = record(v.enrichment);
  if (
    t.timebase !== "source-pts" ||
    !uint(t.width) ||
    !t.width ||
    !uint(t.height) ||
    !t.height ||
    !uint(e.revision) ||
    !Array.isArray(t.pixel_to_display) ||
    t.pixel_to_display.length !== 6 ||
    !t.pixel_to_display.every(Number.isFinite)
  )
    throw Error("invalid_timeline");
  if (
    v.media_available &&
    (!v.source ||
      v.source.url !== "/api/v1/video-jobs/" + id + "/playback/source")
  )
    throw Error("invalid_source");
  return v as Playback;
}
export function validateFramePage(
  value: unknown,
  state: Playback,
  start: number,
  end: number,
): FramePage {
  const v = record(value);
  if (
    v.job_id !== state.job_id ||
    v.generation !== state.generation ||
    v.snapshot !== state.revision ||
    v.from_us !== start ||
    v.to_us !== end ||
    !Array.isArray(v.frames) ||
    !v.frames.length ||
    v.frames.length > 100 ||
    (v.next_cursor !== null &&
      (typeof v.next_cursor !== "string" || v.next_cursor.length > 512))
  )
    throw Error("invalid_frame_page");
  for (const f of v.frames) {
    if (
      ![
        f.frame_index,
        f.start_us,
        f.end_us,
        f.observation_offset,
        f.observation_total,
      ].every(uint) ||
      f.end_us <= f.start_us ||
      f.end_us > state.available_until_us ||
      !Array.isArray(f.observations) ||
      f.observations.length > 1000 ||
      f.observation_offset + f.observations.length > f.observation_total
    )
      throw Error("invalid_frame");
    f.observations.forEach((o: Observation, i: number) => {
      if (
        !uint(o.track_id) ||
        !o.track_id ||
        o.ordinal !== f.observation_offset + i ||
        !Number.isFinite(o.confidence) ||
        o.confidence < 0 ||
        o.confidence > 1
      )
        throw Error("invalid_observation");
      for (const b of [o.raw_bbox, o.display_bbox].filter(Boolean) as Box[]) {
        if (
          !Object.values(b).every(uint) ||
          b.x_max <= b.x_min ||
          b.y_max <= b.y_min ||
          b.x_max > state.timeline.width ||
          b.y_max > state.timeline.height
        )
          throw Error("invalid_box");
      }
    });
  }
  return v as FramePage;
}
export function clampSeek(us: number, state: Playback) {
  return Math.max(0, Math.min(Math.round(us), state.last_frame_start_us ?? 0));
}
export const terminal = (s: Playback) =>
  ["complete", "partial_failed"].includes(s.analysis_state);
