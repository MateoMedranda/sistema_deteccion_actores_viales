import {it,expect} from 'vitest';import {directionArrow} from '../../../src/features/video-analysis/directionArrow';
it('normal arrow is perpendicular in source pixels, including non-square scenes',()=>{
 const line={point_a:{x:.1,y:.2},point_b:{x:.8,y:.6}};const a=directionArrow(line,1920,1080,'negative_to_positive');
 const b=directionArrow(line,1920,1080,'positive_to_negative');
 const dx=(line.point_b.x-line.point_a.x)*1920,dy=(line.point_b.y-line.point_a.y)*1080;
 expect(dx*(a.x2-a.x1)+dy*(a.y2-a.y1)).toBeCloseTo(0,5);expect(a.x1).toBeCloseTo(b.x2);expect(a.y1).toBeCloseTo(b.y2);
});


import {renderHook,act,waitFor} from '@testing-library/react';import {vi} from 'vitest';
import {useDirectedCount} from '../../../src/features/video-analysis/useDirectedCount';
const gen='11111111-1111-4111-8111-111111111111';
const base:any={job_id:'test',generation:gen,policy_version:'finite-center-v1',revision:0,enabled:false,line:null,direction:null,status:'disabled',at_us:0,available_until_us:5000000,covered_until_us:5000000,total:0,error_code:null,expires_at:'2099-01-01T00:00:00Z'};
const playback:any={generation:gen,last_frame_start_us:4900000,expires_at:base.expires_at};
it('ignores a late navigation result while still returning revision data for mutations',async()=>{
 let resolve!:(v:any)=>void;const client={json:vi.fn().mockImplementationOnce(()=>new Promise(r=>resolve=r)).mockResolvedValue({...base,at_us:100000})};
 const view=renderHook(()=>useDirectedCount(client as any,'test',playback,0,true,vi.fn()));await waitFor(()=>expect(client.json).toHaveBeenCalled());
 await act(async()=>{view.result.current.refresh(100000);await Promise.resolve()});await waitFor(()=>expect(view.result.current.result?.at_us).toBe(100000));
 await act(async()=>resolve(base));expect(view.result.current.result?.at_us).toBe(100000);
});
it('conciliates an accepted PUT with a lost response without posting again',async()=>{
 let server={...base};const line={point_a:{x:.1,y:.5},point_b:{x:.9,y:.5}};
 const client={json:vi.fn(async(_path:string,init?:RequestInit)=>{if(init?.method==='PUT'){const body=JSON.parse(init.body as string);server={...server,enabled:true,line:body.line,direction:body.direction,revision:1,status:'ready'};throw Error('lost response')}return server})};
 const view=renderHook(()=>useDirectedCount(client as any,'test',playback,0,true,vi.fn()));await waitFor(()=>expect(view.result.current.result).toBeDefined());
 await act(async()=>{await view.result.current.configure(line,'negative_to_positive')});expect(view.result.current.result?.revision).toBe(1);expect(view.result.current.message).toBe('');expect(client.json.mock.calls.filter(c=>c[1]?.method==='PUT')).toHaveLength(1);
});
