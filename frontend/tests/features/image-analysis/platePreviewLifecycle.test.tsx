import {renderHook,act,waitFor} from "@testing-library/react";
import {expect,it,vi} from "vitest";
import {usePlatePreview} from "../../../src/features/image-analysis/usePlatePreview";
const base={sourceId:"s",jobId:"j",detectionId:1,box:{x_min:1,y_min:1,x_max:3,y_max:3},expiresAt:Date.now()+60000};
it("revokes a selection, rejects late evidence and modes never request",async()=>{
 let resolve!:(v:any)=>void;
 const client:any={platePreview:vi.fn().mockImplementationOnce(()=>new Promise(r=>resolve=r)).mockResolvedValue({blob:new Blob(),metadata:{expires_at:new Date(Date.now()+30000).toISOString()}})};
 const revoke=vi.spyOn(URL,"revokeObjectURL");
 const {result,rerender,unmount}=renderHook(({ctx})=>usePlatePreview(client,ctx),{initialProps:{ctx:base}});
 rerender({ctx:{...base,detectionId:2}});
 await waitFor(()=>expect(result.current.status).toBe("available"));
 const url=result.current.url;
 await act(async()=>resolve({blob:new Blob(),metadata:{}}));
 expect(result.current.url).toBe(url);
 act(()=>{result.current.setView("processed");result.current.setZoom(4);});
 expect(client.platePreview).toHaveBeenCalledTimes(2);
 unmount();expect(revoke).toHaveBeenCalledWith(url);
});
it("does not fetch when localization is unavailable",()=>{
 const client:any={platePreview:vi.fn()};
 const {result}=renderHook(()=>usePlatePreview(client,undefined));
 expect(result.current.status).toBe("idle");expect(client.platePreview).not.toHaveBeenCalled();
});
