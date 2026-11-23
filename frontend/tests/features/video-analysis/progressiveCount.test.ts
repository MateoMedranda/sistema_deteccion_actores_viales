import {act,renderHook} from "@testing-library/react";
import {afterEach,it,expect,vi} from "vitest";
import {ApiClient,ClientError} from "../../../src/services/apiClient";
import {useProgressiveCount} from "../../../src/features/video-analysis/useProgressiveCount";
import type {Playback} from "../../../src/features/video-analysis/progressiveTypes";
afterEach(()=>vi.useRealTimers());
it("recovers an ambiguously accepted line without repeating its mutation",async()=>{
 vi.useFakeTimers();let accepted=false;
 const line={point_a:{x:0,y:.5},point_b:{x:1,y:.5}};
 const json=vi.fn(async(_path:string,init?:RequestInit)=>{if(init?.method==="PUT"){accepted=true;throw new ClientError(0,{code:"network_unavailable",message:"network"})}return {job_id:"job",generation:"g",enabled:accepted,line:accepted?line:null,revision:accepted?1:0,at_us:0,available_until_us:100000,total:0,a_to_b:0,b_to_a:0}});
 const client={json} as unknown as ApiClient;const state={generation:"g",media_available:true,last_frame_start_us:0,expires_at:new Date(Date.now()+60000).toISOString()} as Playback;const unavailable=vi.fn();
 const hook=renderHook(()=>useProgressiveCount(client,"job",state,0,true,unavailable));
 await act(async()=>{await Promise.resolve()});expect(hook.result.current.result?.enabled).toBe(false);
 await act(async()=>{await hook.result.current.configure(line)});
 await act(async()=>{await vi.advanceTimersByTimeAsync(500)});
 expect(hook.result.current.result?.enabled).toBe(true);expect(json.mock.calls.filter(c=>c[1]?.method==="PUT")).toHaveLength(1);expect(unavailable).not.toHaveBeenCalled();hook.unmount();
});
