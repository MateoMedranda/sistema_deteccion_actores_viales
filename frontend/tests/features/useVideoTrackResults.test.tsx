import {renderHook,act,waitFor} from "@testing-library/react";
import {it,expect,vi} from "vitest";
import {useVideoTrackResults} from "../../src/features/video-analysis/useVideoTrackResults";
import {vehicleResult} from "../fixtures/imageAnalysis";
it("replaces pages, uses 25 results and ignores a late page after identity changes",async()=>{
 const expiresAt=Date.now()+60000;let late:any;const c={enrichmentResults:vi.fn(async(id:string,page:number,size:number)=>{if(id==="old")return new Promise(r=>late=r);return {page,page_size:size,total:61,items:[{...vehicleResult(page),track_id:page*41}]};})};
 const {result,rerender}=renderHook(({id})=>useVideoTrackResults(c as any,{identity:id,jobId:id,expiresAt}),{initialProps:{id:"old"}});
 rerender({id:"new"});await waitFor(()=>expect(result.current.state.status).toBe("ready"));
 await act(async()=>late({page:1,page_size:25,total:1,items:[{...vehicleResult(),track_id:1}]}));expect(result.current.state.page?.items[0].track_id).toBe(41);
 await act(async()=>{await result.current.load(3);});await waitFor(()=>expect(result.current.state.page?.page).toBe(3));expect(result.current.state.page?.items[0].track_id).toBe(123);expect(c.enrichmentResults.mock.calls.at(-1)?.slice(0,3)).toEqual(["new",3,25]);
 act(()=>result.current.select(123));expect(result.current.state.selected?.track_id).toBe(123);
});
