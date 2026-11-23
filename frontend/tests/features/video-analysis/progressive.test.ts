import { describe, it, expect } from "vitest";
import { FrameCache } from "../../../src/features/video-analysis/frameCache";
import {
  clampSeek,
  type Playback,
} from "../../../src/features/video-analysis/progressiveTypes";
const state = {
  job_id: "a",
  generation: "g",
  revision: 1,
  available_until_us: 200,
  last_frame_start_us: 100,
  timeline: { width: 64, height: 48 },
} as Playback;
const f = (index: number) => ({
  frame_index: index,
  start_us: index * 100,
  end_us: (index + 1) * 100,
  pts: String(index),
  observation_offset: 0,
  observation_total: 0,
  observations: [],
});
const page = (frames: unknown[], next_cursor: string | null = null) => ({
  job_id: "a",
  generation: "g",
  snapshot: 1,
  from_us: 0,
  to_us: 200,
  frames,
  next_cursor,
});
describe("confirmed video prefix", () => {
  it("clamps future seeks to the last frame start, including the exclusive end", () => {
    expect(clampSeek(200, state)).toBe(100);
    expect(clampSeek(-20, state)).toBe(0);
    expect(clampSeek(30, state)).toBe(30);
  });
  it("admits analyzed empty frames only after the entire window is received", async () => {
    const c = new FrameCache();
    await c.load(
      state,
      0,
      200,
      async () => page([f(0), f(1)]),
      new AbortController().signal,
    );
    expect(c.frame(199)?.frame_index).toBe(1);
    expect(c.frame(200)).toBeUndefined();
  });
  it("rejects gaps, incomplete parts and mismatched generations", async () => {
    for (const frames of [[f(1)], [{ ...f(0), observation_total: 1 }, f(1)]])
      await expect(
        new FrameCache().load(
          state,
          0,
          200,
          async () => page(frames),
          new AbortController().signal,
        ),
      ).rejects.toThrow();
    await expect(
      new FrameCache().load(
        state,
        0,
        200,
        async () => ({ ...page([f(0), f(1)]), generation: "old" }),
        new AbortController().signal,
      ),
    ).rejects.toThrow();
  });
  it("does not publish a partially downloaded window", async () => {
    const c = new FrameCache();
    let calls = 0;
    await expect(
      c.load(
        state,
        0,
        200,
        async () => {
          if (calls++) throw Error("offline");
          return page([f(0)], "next");
        },
        new AbortController().signal,
      ),
    ).rejects.toThrow();
    expect(c.frame(0)).toBeUndefined();
  });
});
