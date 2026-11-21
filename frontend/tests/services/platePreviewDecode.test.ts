import {it,expect,vi,afterEach} from "vitest";
import {ApiClient} from "../../src/services/apiClient";
import * as decoder from "../../src/utils/decodeImage";
const ctx=()=>({sourceId:"s",jobId:"j",detectionId:1,box:{x_min:0,y_min:0,x_max:20,y_max:10},expiresAt:Date.now()+60000});
const metadata=()=>({version:1,source_id:"s",enrichment_job_id:"j",detection_id:1,profile_id:"display-contrast-v1",input_size:{width:20,height:10},output_size:{width:80,height:40},original_bbox:ctx().box,applied_steps:["grayscale","resize_integer","clahe"],original_to_processed:[4,0,0,0,4,0],expires_at:new Date(Date.now()+30000).toISOString()});
function response(){return new Response(new Uint8Array([137,80,78,71,13,10,26,10,0]),{headers:{"Content-Type":"image/png","X-Plate-Preview-Metadata":JSON.stringify(metadata())}});}
afterEach(()=>{vi.useRealTimers();vi.unstubAllGlobals();vi.restoreAllMocks();});
it("publishes only decoded dimensions matching metadata and revokes the validation URL",async()=>{
 vi.stubGlobal("fetch",vi.fn(async()=>response()));
 vi.spyOn(decoder,"decodeImage").mockResolvedValue({width:80,height:40});
 const revoke=vi.spyOn(URL,"revokeObjectURL"),client=new ApiClient("http://localhost:8000","key");
 expect((await client.platePreview(ctx())).metadata.output_size.width).toBe(80);
 expect(revoke).toHaveBeenCalled();
 vi.mocked(decoder.decodeImage).mockResolvedValue({width:79,height:40});
 await expect(client.platePreview(ctx())).rejects.toMatchObject({detail:{code:"invalid_response"}});
});
it("the total budget includes a decoder which never completes",async()=>{
 vi.useFakeTimers();vi.stubGlobal("fetch",vi.fn(async()=>response()));
 vi.spyOn(HTMLImageElement.prototype,"decode").mockImplementation(()=>new Promise(()=>{}));
 const client=new ApiClient("http://localhost:8000","key"),revoke=vi.spyOn(URL,"revokeObjectURL");
 const assertion=expect(client.platePreview(ctx(),{timeoutMs:40})).rejects.toMatchObject({detail:{code:"request_timeout"}});
 await vi.advanceTimersByTimeAsync(41);await assertion;expect(revoke).toHaveBeenCalled();
});

it("shortens the complete body budget to the authenticated metadata expiry",async()=>{
 vi.useFakeTimers();const m=metadata();m.expires_at=new Date(Date.now()+30).toISOString();
 vi.stubGlobal("fetch",vi.fn(async()=>new Response(new ReadableStream({start(){}}),{headers:{"Content-Type":"image/png","X-Plate-Preview-Metadata":JSON.stringify(m)}})));
 const p=new ApiClient("http://localhost:8000","key").platePreview(ctx());
 const assertion=expect(p).rejects.toMatchObject({status:410});
 await vi.advanceTimersByTimeAsync(31);await assertion;
});
