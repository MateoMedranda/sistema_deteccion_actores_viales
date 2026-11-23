import type { Frame, FramePage, Playback } from "./progressiveTypes";
import { validateFramePage } from "./progressiveTypes";
type Window = {
  start: number;
  end: number;
  frames: Frame[];
  bytes: number;
  used: number;
};
export class FrameCache {
  private windows = new Map<number, Window>();
  private clock = 0;
  clear() {
    this.windows.clear();
  }
  get bytes() {
    return [...this.windows.values()].reduce((n, w) => n + w.bytes, 0);
  }
  get duration() {
    return [...this.windows.values()].reduce((n, w) => n + w.end - w.start, 0);
  }
  frame(us: number) {
    for (const w of this.windows.values()) {
      const f = w.frames.find((f) => f.start_us <= us && us < f.end_us);
      if (f) {
        w.used = ++this.clock;
        return f;
      }
    }
  }
  covers(start: number, end: number) {
    return [...this.windows.values()].some(
      (w) => w.start <= start && w.end >= end,
    );
  }
  async load(
    state: Playback,
    start: number,
    end: number,
    get: (cursor?: string) => Promise<unknown>,
    signal: AbortSignal,
  ) {
    if (this.covers(start, end)) return;
    const parts = new Map<number, Frame>();
    let cursor: string | undefined;
    const seen = new Set<string>();
    let bytes = 0;
    do {
      if (signal.aborted) throw new DOMException("Aborted", "AbortError");
      const page = validateFramePage(
        await get(cursor),
        state,
        start,
        end,
      ) as FramePage;
      bytes += JSON.stringify(page).length * 2;
      if (bytes > 16 * 1024 * 1024) throw Error("annotation_window_too_dense");
      for (const f of page.frames) {
        const prior = parts.get(f.frame_index);
        if (prior) {
          if (
            f.observation_offset !== prior.observations.length ||
            f.observation_total !== prior.observation_total ||
            f.start_us !== prior.start_us ||
            f.end_us !== prior.end_us
          )
            throw Error("incomplete_frame");
          prior.observations.push(...f.observations);
        } else {
          if (f.observation_offset !== 0) throw Error("incomplete_frame");
          parts.set(f.frame_index, { ...f, observations: [...f.observations] });
        }
      }
      cursor = page.next_cursor ?? undefined;
      if (cursor) {
        if (seen.has(cursor)) throw Error("repeated_cursor");
        seen.add(cursor);
      }
    } while (cursor);
    if (signal.aborted) throw new DOMException("Aborted", "AbortError");
    const frames = [...parts.values()].sort(
      (a, b) => a.frame_index - b.frame_index,
    );
    if (
      !frames.length ||
      frames[0].start_us > start ||
      frames.at(-1)!.end_us < end
    )
      throw Error("annotation_gap");
    frames.forEach((f, i) => {
      if (
        f.observations.length !== f.observation_total ||
        (i > 0 &&
          (frames[i - 1].end_us !== f.start_us ||
            frames[i - 1].frame_index + 1 !== f.frame_index))
      )
        throw Error("annotation_gap");
    });
    this.windows.set(start, { start, end, frames, bytes, used: ++this.clock });
    while (this.bytes > 16 * 1024 * 1024 || this.duration > 30_000_000) {
      const oldest = [...this.windows.entries()].sort(
        (a, b) => a[1].used - b[1].used,
      )[0];
      this.windows.delete(oldest[0]);
    }
  }
}
