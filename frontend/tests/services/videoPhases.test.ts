import {it,expect} from "vitest";
import {parseVideoJob} from "../../src/services/apiTypes";
const base={job_id:"video",status:"processing",processed_frames:3,total_frames:3,progress_percent:100,expires_at:"2040-01-01T00:00:00Z"};
it("does not equate 100 percent frames with ready and accepts legacy unknown",()=>{
 expect(parseVideoJob(base).processing_phase).toBeNull();expect(parseVideoJob(base).frame_total_confirmed).toBe(false);
 expect(parseVideoJob({...base,processing_phase:"encoding",frame_total_confirmed:true}).video_metadata).toBeNull();
 expect(()=>parseVideoJob({...base,frame_total_confirmed:null})).toThrow();
 expect(()=>parseVideoJob({...base,processing_phase:"ready",frame_total_confirmed:true})).toThrow();
});
