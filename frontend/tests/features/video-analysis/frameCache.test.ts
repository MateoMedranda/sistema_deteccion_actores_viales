import {it,expect} from 'vitest';import {FrameCache} from '../../../src/features/video-analysis/frameCache';import type {Playback} from '../../../src/features/video-analysis/progressiveTypes';
it('never publishes a partial annotation window if navigation aborts between pages',async()=>{const cache=new FrameCache(),abort=new AbortController();const state={job_id:'a',generation:'g',revision:1,available_until_us:200,last_frame_start_us:100,timeline:{width:64,height:48}} as Playback;let requests=0;const get=async()=>{requests++;abort.abort();return {job_id:'a',generation:'g',snapshot:1,from_us:0,to_us:200,frames:[{frame_index:0,start_us:0,end_us:100,pts:'0',observation_offset:0,observation_total:0,observations:[]}],next_cursor:'next'}};await expect(cache.load(state,0,200,get,abort.signal)).rejects.toThrow();expect(requests).toBe(1);expect(cache.frame(0)).toBeUndefined();expect(cache.bytes).toBe(0)});

it('rejects an oversized annotation window without replacing a previously admitted one',async()=>{
 const c=new FrameCache(),state={job_id:'a',generation:'g',revision:1,available_until_us:200,timeline:{width:64,height:48}} as Playback;
 const page=(start:number,end:number,padding='')=>({job_id:'a',generation:'g',snapshot:1,from_us:start,to_us:end,frames:[{frame_index:start/100,start_us:start,end_us:end,pts:String(start),observation_offset:0,observation_total:0,observations:[]}],next_cursor:null,padding});
 await c.load(state,0,100,async()=>page(0,100),new AbortController().signal);const bytes=c.bytes;
 await expect(c.load(state,100,200,async()=>page(100,200,'x'.repeat(9*1024*1024)),new AbortController().signal)).rejects.toThrow('annotation_window_too_dense');expect(c.bytes).toBe(bytes);expect(c.bytes).toBeLessThanOrEqual(16*1024*1024);expect(c.frame(0)?.frame_index).toBe(0);expect(c.frame(100)).toBeUndefined();
});
it('evicts old annotation windows while navigating beyond the 30-second cache',async()=>{
 const c=new FrameCache(),state={job_id:'a',generation:'g',revision:1,available_until_us:40000000,timeline:{width:64,height:48}} as Playback;
 for(let i=0;i<8;i++){
  const start=i*5000000,end=start+5000000;await c.load(state,start,end,async()=>({job_id:'a',generation:'g',snapshot:1,from_us:start,to_us:end,frames:[{frame_index:i,start_us:start,end_us:end,pts:String(i),observation_offset:0,observation_total:0,observations:[]}],next_cursor:null}),new AbortController().signal);
  expect(c.duration).toBeLessThanOrEqual(30000000);expect(c.bytes).toBeLessThanOrEqual(16*1024*1024);
 }expect(c.frame(0)).toBeUndefined();expect(c.frame(35000000)?.frame_index).toBe(7);
});
