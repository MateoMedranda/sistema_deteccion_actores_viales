import {it,expect,vi} from "vitest";
import {ApiClient} from "../../src/services/apiClient";
it("managed requests send session headers, never a backend key",async()=>{
 const fetcher=vi.fn(async()=>new Response(JSON.stringify({status:"alive"}),{status:200,headers:{"Content-Type":"application/json"}}));vi.stubGlobal("fetch",fetcher);
 try{const client=new ApiClient("http://localhost/web-api","",{csrf:"web-token",expiresAt:Date.now()+60000});await client.video("synthetic");
 const [url,init]=fetcher.mock.calls[0] as unknown as [string,RequestInit];
 expect(url).toBe("http://localhost/web-api/api/v1/video-jobs/synthetic");
 const h=new Headers(init.headers);expect(h.get("X-API-Key")).toBeNull();expect(h.get("X-UI-CSRF")).toBe("web-token");expect(init.credentials).toBe("same-origin");
 await expect(client.originalImage("http://localhost/private")).rejects.toThrow();
 }finally{vi.unstubAllGlobals();}
});
