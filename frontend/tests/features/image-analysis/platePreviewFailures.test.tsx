import {renderHook,act,waitFor} from "@testing-library/react";
import {it,expect,vi,afterEach} from "vitest";
import {usePlatePreview} from "../../../src/features/image-analysis/usePlatePreview";
import {ClientError} from "../../../src/services/apiClient";
const context=()=>({sourceId:"s",jobId:"j",detectionId:1,box:{x_min:1,y_min:1,x_max:20,y_max:10},expiresAt:Date.now()+60000});
afterEach(()=>vi.useRealTimers());
it.each([401,404,410])("forwards access %s immediately and retires late work",async status=>{
 const rejected=vi.fn(),client:any={platePreview:vi.fn().mockRejectedValue(new ClientError(status,{code:"access_unavailable",message:"safe"}))};
 const ctx=context();const {result,unmount}=renderHook(()=>usePlatePreview(client,ctx,rejected));
 await waitFor(()=>expect(result.current.status).toBe("expired"));
 expect(rejected).toHaveBeenCalledTimes(1);expect(result.current.url).toBeUndefined();unmount();
});
it.each([409,422,429,504])("keeps failure %s separate from access and retries only the GET",async status=>{
 const rejected=vi.fn(),client:any={platePreview:vi.fn().mockRejectedValue(new ClientError(status,{code:"safe_failure",message:"safe"}))};
 const ctx=context(),{result,unmount}=renderHook(()=>usePlatePreview(client,ctx,rejected));
 await waitFor(()=>expect(result.current.status).toBe(status===422?"not_applicable":"failed"));
 expect(rejected).not.toHaveBeenCalled();
 if(status!==422){act(()=>result.current.retry());await waitFor(()=>expect(client.platePreview).toHaveBeenCalledTimes(2));}
 unmount();
});
it("TTL revokes available evidence without another request",async()=>{
 vi.useFakeTimers();const ctx=context();ctx.expiresAt=Date.now()+100;
 const client:any={platePreview:vi.fn().mockResolvedValue({blob:new Blob(),metadata:{expires_at:new Date(ctx.expiresAt).toISOString()}})};
 const revoke=vi.spyOn(URL,"revokeObjectURL");
 const {result,unmount}=renderHook(()=>usePlatePreview(client,ctx));
 await act(async()=>{await Promise.resolve();});
 const url=result.current.url;expect(result.current.status).toBe("available");
 await act(async()=>vi.advanceTimersByTimeAsync(101));
 expect(result.current.status).toBe("expired");expect(revoke).toHaveBeenCalledWith(url);expect(client.platePreview).toHaveBeenCalledTimes(1);unmount();
});
