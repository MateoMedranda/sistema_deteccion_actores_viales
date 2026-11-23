import {describe,it,expect} from "vitest";
import {playbackDecision} from "../../../src/features/video-analysis/playbackPolicy";
import type {Playback} from "../../../src/features/video-analysis/progressiveTypes";
const state=(available=5_000_000,analysis_state:Playback["analysis_state"]="analyzing")=>({available_until_us:available,buffer_seconds:5,analysis_state}) as Playback;
describe("playback intent and analyzed buffer",()=>{
 it("waits below five seconds and plays only with the complete annotations",()=>{expect(playbackDecision(state(4_999_999),0,true,true)).toBe("wait");expect(playbackDecision(state(),0,true,false)).toBe("wait");expect(playbackDecision(state(),0,true,true)).toBe("play");});
 it("a growing prefix never resumes a manual pause",()=>{for(const n of [5_000_000,10_000_000,20_000_000])expect(playbackDecision(state(n),0,false,true)).toBe("pause");});
 it("terminal short tails and partial failures can be inspected, but their exclusive end cannot play",()=>{for(const s of ["complete","partial_failed"] as const){expect(playbackDecision(state(100000,s),0,true,true)).toBe("play");expect(playbackDecision(state(100000,s),100000,true,true)).toBe("wait");}});
 it("natural completion remains ended until a new user action",()=>{expect(playbackDecision(state(100000,"complete"),100000,true,true,true)).toBe("ended");});
});
