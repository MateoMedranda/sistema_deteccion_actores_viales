import {StrictMode} from "react";
import {act,renderHook} from "@testing-library/react";
import {it,expect,vi} from "vitest";
import {useManagedSession} from "../../src/hooks/useManagedSession";
const ready=(n:number,ttl=60000)=>new Response(JSON.stringify({status:"ready",epoch:"00000000-0000-4000-8000-"+String(n).padStart(12,"0"),csrf_token:"c".repeat(43),expires_at:new Date(Date.now()+ttl).toISOString(),policy:{image:{media_types:["image/png"],max_upload_bytes:100000,max_image_pixels:100000},video:{media_types:["video/mp4"],max_upload_bytes:100000,max_duration_seconds:120,max_width:1920,max_height:1080,max_fps:30,max_frames:3600},capabilities:{image_detection:true,video_analysis:true,attributes:true,plates:true}}}),{headers:{"Content-Type":"application/json"}});
it("recovers a failed bootstrap automatically with one request at a time",async()=>{
 vi.useFakeTimers();const fetcher=vi.fn().mockRejectedValueOnce(new TypeError("offline")).mockImplementation(async()=>ready(1));
 vi.stubGlobal("fetch",fetcher);
 const view=renderHook(()=>useManagedSession(),{wrapper:StrictMode});
 try{
  await act(async()=>{});expect(fetcher).toHaveBeenCalledTimes(1);expect(view.result.current.state).toBe("upstream_unavailable");
  await act(async()=>vi.advanceTimersByTimeAsync(1999));expect(fetcher).toHaveBeenCalledTimes(1);
  await act(async()=>vi.advanceTimersByTimeAsync(1));expect(fetcher).toHaveBeenCalledTimes(2);expect(view.result.current.state).toBe("ready");
  await act(async()=>vi.advanceTimersByTimeAsync(10000));expect(fetcher).toHaveBeenCalledTimes(2);
 }finally{view.unmount();vi.useRealTimers();vi.unstubAllGlobals();}
});
it("reconnects after absolute expiry and replaces the client without manual action",async()=>{
 vi.useFakeTimers();let count=0;vi.stubGlobal("fetch",vi.fn(async()=>ready(++count,1000)));
 const view=renderHook(()=>useManagedSession());
 try{
  await act(async()=>{});const old=view.result.current.client;expect(count).toBe(1);
  await act(async()=>vi.advanceTimersByTimeAsync(1000));
  expect(count).toBe(2);expect(view.result.current.state).toBe("ready");expect(view.result.current.client).not.toBe(old);
  expect(view.result.current.session?.epoch.endsWith("000000000002")).toBe(true);
 }finally{view.unmount();vi.useRealTimers();vi.unstubAllGlobals();}
});
