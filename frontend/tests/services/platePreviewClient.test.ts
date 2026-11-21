import {it,expect,vi,afterEach} from "vitest";
import {ApiClient} from "../../src/services/apiClient";
import {parsePlatePreviewMetadata} from "../../src/services/apiTypes";
const bbox={x_min:10,y_min:10,x_max:30,y_max:20};
export const context={sourceId:"source",jobId:"job",detectionId:1,box:bbox,expiresAt:Date.now()+60000};
const metadata=()=>({version:1,source_id:"source",enrichment_job_id:"job",detection_id:1,profile_id:"display-contrast-v1",input_size:{width:20,height:10},output_size:{width:80,height:40},original_bbox:bbox,applied_steps:["grayscale","resize_integer","clahe"],original_to_processed:[4,0,0,0,4,0],expires_at:new Date(Date.now()+30000).toISOString()});
afterEach(()=>{vi.useRealTimers();vi.unstubAllGlobals();});
it("validates every metadata association and geometry before publication",()=>{
 expect(parsePlatePreviewMetadata(metadata(),context).detection_id).toBe(1);
 for(const bad of [{...metadata(),source_id:"other"},{...metadata(),original_to_processed:[4,0,1,0,4,0]},{...metadata(),output_size:{width:79,height:40}},{...metadata(),extra:"bad"}])
 expect(()=>parsePlatePreviewMetadata(bad,context)).toThrow();
});
it("rejects missing provenance and oversized streams",async()=>{
 const client=new ApiClient("http://localhost:8000","key");
 vi.stubGlobal("fetch",vi.fn(async()=>new Response("bad",{headers:{"Content-Type":"image/png"}})));
 await expect(client.platePreview(context)).rejects.toMatchObject({detail:{code:"invalid_response"}});
 vi.stubGlobal("fetch",vi.fn(async()=>new Response(new Uint8Array(2*1024*1024+1),{headers:{"Content-Type":"image/png","X-Plate-Preview-Metadata":JSON.stringify(metadata())}})));
 await expect(client.platePreview(context)).rejects.toMatchObject({detail:{code:"invalid_response"}});
});
it("includes a suspended body in the total deadline",async()=>{
 vi.useFakeTimers();
 vi.stubGlobal("fetch",vi.fn(async()=>new Response(new ReadableStream({start(){}}),{headers:{"Content-Type":"image/png","X-Plate-Preview-Metadata":JSON.stringify(metadata())}})));
 const client=new ApiClient("http://localhost:8000","key");
 const p=expect(client.platePreview(context,{timeoutMs:30})).rejects.toMatchObject({detail:{code:"request_timeout"}});
 await vi.advanceTimersByTimeAsync(31);await p;
});
it.each([401,404,410])("withdraws %s immediately without an error body",async status=>{
 const body=vi.fn(()=>new Promise(()=>{}));
 vi.stubGlobal("fetch",vi.fn(async()=>({ok:false,status,json:body})));
 await expect(new ApiClient("http://localhost:8000","key").platePreview(context)).rejects.toMatchObject({status});
 expect(body).not.toHaveBeenCalled();
});
