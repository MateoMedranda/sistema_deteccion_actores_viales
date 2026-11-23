import {afterEach,it,expect,vi} from "vitest";
import {ApiClient} from "../../../src/services/apiClient";
const client=()=>new ApiClient("http://localhost/web-api","",{csrf:"token",expiresAt:Date.now()+60000});
afterEach(()=>vi.unstubAllGlobals());
it("validates an authenticated bounded range and refuses another generation",async()=>{
 const key='"generation-4"';
 const fetch=vi.fn().mockResolvedValue(new Response(new Uint8Array([1,2]),{status:206,headers:{"Content-Range":"bytes 0-1/4",ETag:key}}));
 vi.stubGlobal("fetch",fetch);
 expect([...new Uint8Array(await client().sourceRange("job","generation",4,0,1))]).toEqual([1,2]);
 expect(fetch.mock.calls[0][1].headers.Range).toBe("bytes=0-1");
 expect(fetch.mock.calls[0][1].headers["X-UI-CSRF"]).toBe("token");
 fetch.mockResolvedValue(new Response(new Uint8Array([1,2]),{status:206,headers:{"Content-Range":"bytes 0-1/4",ETag:'"other"'}}));
 await expect(client().sourceRange("job","generation",4,0,1)).rejects.toMatchObject({detail:{code:"invalid_media_range"}});
});
