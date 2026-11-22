import {renderHook,act,waitFor} from "@testing-library/react";
import {it,expect,vi} from "vitest";
import {useVideoAnalysis} from "../../src/features/video-analysis/useVideoAnalysis";
const job={job_id:"video",status:"completed",progress_percent:100,processed_frames:10,total_frames:10,expires_at:"2040-01-01T00:00:00Z",processing_phase:"ready",frame_total_confirmed:true,video_metadata:{width:640,height:360,fps:10,frame_count:10,duration_seconds:1,timebase:"processed-cfr"},eligible_track_count:1,classes_present:["car"]};
it("starts one enrichment, fetches real state after acceptance, and does not repeat video on retry",async()=>{
 const c={newVideoIntent:vi.fn(()=>({intent:crypto.randomUUID(),intentGeneration:1})),uploadVideo:vi.fn(async()=>({job_id:"video",status:"queued"})),video:vi.fn(async()=>job),enrich:vi.fn(async()=>({enrichment_job_id:"enrich",status:"queued"})),enrichment:vi.fn(async()=>({enrichment_job_id:"enrich",source:{kind:"video",source_id:"video"},status:"failed",expires_at:"2040-01-01T00:00:00Z",processed_units:0,total_units:1,progress_percent:0,results_ready:0})),cancelVideo:vi.fn(),cancelEnrichment:vi.fn()};
 const {result}=renderHook(()=>useVideoAnalysis(c as any));
 act(()=>result.current.choose(new File(["x"],"video.mp4",{type:"video/mp4"})));
 await act(async()=>{await Promise.all([result.current.start(),result.current.start()]);});
 await waitFor(()=>expect(result.current.state.processing).toBe("ready"));
 expect(c.uploadVideo).toHaveBeenCalledTimes(1);expect(c.enrich).toHaveBeenCalledTimes(1);expect(c.video).toHaveBeenCalled();
 await act(async()=>result.current.retryEnrichment());
 expect(c.uploadVideo).toHaveBeenCalledTimes(1);expect(c.enrich).toHaveBeenCalledTimes(2);
});

it("recovers a lost upload receipt with exactly the same intent and skips noneligible enrichment",async()=>{
 const {ClientError}=await import("../../src/services/apiClient");
 const c={newVideoIntent:vi.fn(()=>({intent:crypto.randomUUID(),intentGeneration:1})),uploadVideo:vi.fn().mockRejectedValueOnce(new ClientError(0,{code:"network_unavailable",message:"safe"})).mockResolvedValue({job_id:"video",status:"queued"}),video:vi.fn(async()=>({...job,eligible_track_count:0,classes_present:[]})),enrich:vi.fn(),cancelVideo:vi.fn(),cancelEnrichment:vi.fn()};
 const {result}=renderHook(()=>useVideoAnalysis(c as any));
 act(()=>result.current.choose(new File(["x"],"video.mp4",{type:"video/mp4"})));
 await act(async()=>result.current.start());expect(result.current.state.processing).toBe("interrupted");
 await act(async()=>result.current.resume());expect(result.current.state.enrichment).toBe("not_applicable");
 expect(c.enrich).not.toHaveBeenCalled();expect(c.newVideoIntent).toHaveBeenCalledTimes(1);
 const first=c.uploadVideo.mock.calls[0][1],retry=c.uploadVideo.mock.calls[1][1];expect(retry.intent).toBe(first.intent);expect(retry.intentGeneration).toBe(first.intentGeneration);
});
it("expires the source and drops media even without leaving its workspace",async()=>{
 vi.useFakeTimers();
 const c={newVideoIntent:()=>({intent:crypto.randomUUID(),intentGeneration:1}),uploadVideo:vi.fn(async()=>({job_id:"video"})),video:vi.fn(async()=>({...job,expires_at:new Date(Date.now()+100).toISOString(),eligible_track_count:0})),cancelVideo:vi.fn(),cancelEnrichment:vi.fn()};
 try{const {result}=renderHook(()=>useVideoAnalysis(c as any));act(()=>result.current.choose(new File(["x"],"v.mp4")));
 await act(async()=>result.current.start());expect(result.current.state.video?.job_id).toBe("video");
 await act(async()=>vi.advanceTimersByTime(101));expect(result.current.state.video).toBeUndefined();expect(result.current.state.processing).toBe("expired");expect(result.current.state.file).toBeUndefined();
 }finally{vi.useRealTimers();}
});
