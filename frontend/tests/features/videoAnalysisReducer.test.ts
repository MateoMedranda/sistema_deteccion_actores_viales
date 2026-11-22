import {it,expect} from "vitest";
import {initialVideoState,videoAnalysisReducer} from "../../src/features/video-analysis/videoAnalysisReducer";
it("ignores retired generations and keeps playable media on enrichment failure",()=>{
 const state={...initialVideoState,generation:2,processing:"ready" as const,media:"available" as const,video:{job_id:"video-a"} as any};
 const late=videoAnalysisReducer(state,{type:"processing",generation:1,value:"failed"});
 expect(late).toBe(state);
 const partial=videoAnalysisReducer(state,{type:"enrichment",generation:2,value:"failed"});
 expect(partial.media).toBe("available");expect(partial.processing).toBe("ready");expect(partial.enrichment).toBe("failed");
});
