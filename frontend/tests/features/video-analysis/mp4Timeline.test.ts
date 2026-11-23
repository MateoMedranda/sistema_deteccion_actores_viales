import {readFileSync} from "node:fs";
import path from "node:path";
import {it,expect} from "vitest";
import {readMp4} from "../../../src/features/video-analysis/mp4Timeline";
it("reads a real synthetic MP4 without downloading its full media payload",async()=>{
 const bytes=readFileSync(path.resolve("e2e/fixtures/controlled.mp4"));const ranges:number[][]=[];
 const timeline=await readMp4(bytes.byteLength,async(start,end)=>{ranges.push([start,end]);return Uint8Array.from(bytes.subarray(start,end+1)).buffer;},new AbortController().signal);
 expect(timeline.samples.length).toBeGreaterThan(0);expect(timeline.byDisplay[0].displayIndex).toBe(0);
 expect(timeline.samples.some(s=>s.sample.is_sync)).toBe(true);expect(timeline.rotation).toBe(0);
 expect(timeline.config.codec).toMatch(/^avc/);expect(timeline.config.description?.byteLength).toBeGreaterThan(0);
 expect(ranges.every(([a,b])=>b-a<65536)).toBe(true);
});
