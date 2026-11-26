import {renderHook,act,waitFor} from '@testing-library/react';import {it,expect,vi} from 'vitest';
import fixtures from '../../fixtures/countLines011';import {useCountLines} from '../../../src/features/video-analysis/useCountLines';import {ClientError} from '../../../src/services/apiClient';
const collection=()=>structuredClone(fixtures.valid.find(e=>e.name==='confirmed_collection')!.data) as any;
it('reads back an accepted PUT after losing its response; never resends over another tab',async()=>{
 let server=collection();const client={json:vi.fn(async(_p:string,init?:RequestInit)=>{if(init?.method==='PUT'){const body=JSON.parse(init.body as string);server={...server,revision:server.revision+1,lines:body.lines.map((l:any)=>({...l,geometry_revision:1,origin:'user'}))};throw Error('lost')}return server})};
 const v=renderHook(()=>useCountLines(client as any,'fixture-011',{generation:server.generation,expires_at:server.expires_at} as any,true,vi.fn()));await waitFor(()=>expect(v.result.current.collection).toBeDefined());
 await act(async()=>{await v.result.current.configure(server.lines.map((l:any)=>({...l,name:l.name+' NEW'})))});expect(v.result.current.collection?.revision).toBe(2);expect(client.json.mock.calls.filter(c=>c[1]?.method==='PUT')).toHaveLength(1);
});
it('a capability 404 leaves playback authority intact',async()=>{
 const retire=vi.fn(),client={json:vi.fn().mockRejectedValue(new ClientError(404,{code:'http_error',message:'unavailable'} as any))},server=collection();const v=renderHook(()=>useCountLines(client as any,'fixture-011',{generation:server.generation} as any,true,retire));await waitFor(()=>expect(v.result.current.message).toContain('todavía no admite'));expect(retire).not.toHaveBeenCalled();
});
it('late descriptor from a retired generation is ignored',async()=>{
 let resolve!:(v:unknown)=>void;const old=collection(),fresh={...old,generation:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'},client={json:vi.fn().mockImplementationOnce(()=>new Promise(r=>resolve=r)).mockResolvedValue(fresh)};
 const v=renderHook(({generation})=>useCountLines(client as any,'fixture-011',{generation} as any,true,vi.fn()),{initialProps:{generation:old.generation}});await waitFor(()=>expect(client.json).toHaveBeenCalled());v.rerender({generation:fresh.generation});await waitFor(()=>expect(v.result.current.collection?.generation).toBe(fresh.generation));await act(async()=>resolve(old));expect(v.result.current.collection?.generation).toBe(fresh.generation);
});

it('explains a duplicate color without issuing a PUT or changing confirmed lines',async()=>{const server=collection(),client={json:vi.fn(async()=>server)};const v=renderHook(()=>useCountLines(client as any,'fixture-011',{generation:server.generation} as any,true,vi.fn()));await waitFor(()=>expect(v.result.current.collection).toBeDefined());const next=server.lines.map((l:any)=>({...l,color:server.lines[1].color}));await act(async()=>{await expect(v.result.current.configure(next)).rejects.toThrow('diferentes')});expect(v.result.current.message).toContain('diferentes');expect(client.json).toHaveBeenCalledTimes(1);expect(v.result.current.collection).toEqual(server)});

it('recovers an initial transient descriptor failure without changing workspaces',async()=>{
 const server=collection(),client={json:vi.fn().mockRejectedValueOnce(new ClientError(503,{message:'offline'} as any)).mockResolvedValue(server)};
 const v=renderHook(()=>useCountLines(client as any,server.job_id,{generation:server.generation} as any,true,vi.fn()));
 await waitFor(()=>expect(v.result.current.collection).toEqual(server),{timeout:2000});expect(client.json).toHaveBeenCalledTimes(2);
});
it.each(['job','generation'])('rejects an import response from a foreign %s',async(field)=>{
 const server=collection();server.lines=[];server.legacy_import={status:'offered',line_id:null};
 const foreign={...collection(),legacy_import:{status:'imported',line_id:collection().lines[0].line_id},...(field==='job'?{job_id:'another-job'}:{generation:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'})};
 const client={json:vi.fn(async(_p:string,init?:RequestInit)=>init?.method==='POST'?foreign:server)};
 const v=renderHook(()=>useCountLines(client as any,server.job_id,{generation:server.generation} as any,true,vi.fn()));
 await waitFor(()=>expect(client.json.mock.calls.some(c=>c[1]?.method==='POST')).toBe(true));await waitFor(()=>expect(v.result.current.busy).toBe(false));
 expect(v.result.current.collection?.job_id).toBe(server.job_id);expect(v.result.current.collection?.generation).toBe(server.generation);expect(v.result.current.collection?.lines).toHaveLength(0);
});
it('a late authorization error cannot retire the new generation',async()=>{
 let reject!:(e:unknown)=>void;const old=collection(),fresh={...old,generation:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'},retire=vi.fn();
 const client={json:vi.fn().mockImplementationOnce(()=>new Promise((_r,j)=>reject=j)).mockResolvedValue(fresh)};
 const v=renderHook(({generation})=>useCountLines(client as any,old.job_id,{generation} as any,true,retire),{initialProps:{generation:old.generation}});
 await waitFor(()=>expect(client.json).toHaveBeenCalledTimes(1));v.rerender({generation:fresh.generation});await waitFor(()=>expect(v.result.current.collection?.generation).toBe(fresh.generation));
 await act(async()=>reject(new ClientError(403,{message:'old context'} as any)));expect(retire).not.toHaveBeenCalled();
});
it('reports an admission race specifically and retains the confirmed collection',async()=>{
 const server=collection(),client={json:vi.fn(async(_p:string,init?:RequestInit)=>{if(init?.method==='PUT')throw new ClientError(409,{code:'count_line_admission_limit',message:'limit'} as any);return server})};
 const v=renderHook(()=>useCountLines(client as any,server.job_id,{generation:server.generation} as any,true,vi.fn()));await waitFor(()=>expect(v.result.current.collection).toBeDefined());
 await act(async()=>{await expect(v.result.current.configure(server.lines.map((l:any)=>({...l,name:l.name+' NEW'})))).rejects.toThrow()});expect(v.result.current.message).toMatch(/límite.*identidades/i);expect(v.result.current.collection).toEqual(server);
});

it('retains confirmed lines while a later read recovers automatically',async()=>{
 const server=collection(),fresh={...server,revision:2},client={json:vi.fn().mockResolvedValueOnce(server).mockRejectedValueOnce(new ClientError(503,{message:'offline'} as any)).mockResolvedValue(fresh)};
 const v=renderHook(()=>useCountLines(client as any,server.job_id,{generation:server.generation} as any,true,vi.fn()));await waitFor(()=>expect(v.result.current.collection).toEqual(server));await act(async()=>v.result.current.reload());expect(v.result.current.collection).toEqual(server);await waitFor(()=>expect(v.result.current.collection?.revision).toBe(2));
});
it('cancels scheduled recovery when its context is unmounted',async()=>{
 const server=collection(),client={json:vi.fn().mockRejectedValue(new ClientError(503,{message:'offline'} as any))};
 const v=renderHook(()=>useCountLines(client as any,server.job_id,{generation:server.generation} as any,true,vi.fn()));await waitFor(()=>expect(v.result.current.message).toMatch(/automáticamente/));v.unmount();await new Promise(r=>setTimeout(r,250));expect(client.json).toHaveBeenCalledTimes(1);
});

it.each([401,403,410])('stops descriptor recovery on authority error %i',async(status)=>{
 const server=collection(),retire=vi.fn(),client={json:vi.fn().mockRejectedValue(new ClientError(status,{message:'authority'} as any))};
 const v=renderHook(()=>useCountLines(client as any,server.job_id,{generation:server.generation} as any,true,retire));await waitFor(()=>expect(retire).toHaveBeenCalledTimes(1));await new Promise(r=>setTimeout(r,250));expect(client.json).toHaveBeenCalledTimes(1);v.unmount();
});
it('a late import cannot replace the next video context',async()=>{
 const offered=collection();offered.lines=[];offered.legacy_import={status:'offered',line_id:null};const imported={...collection(),legacy_import:{status:'imported',line_id:collection().lines[0].line_id}},fresh={...collection(),generation:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'};
 let resolve!:(value:unknown)=>void;
 const client={json:vi.fn(async(path:string,init?:RequestInit)=>{if(init?.method==='POST')return new Promise(r=>resolve=r);return path.includes(fresh.generation)?fresh:offered})};
 const v=renderHook(({generation})=>useCountLines(client as any,offered.job_id,{generation} as any,true,vi.fn()),{initialProps:{generation:offered.generation}});await waitFor(()=>expect(resolve).toBeDefined());v.rerender({generation:fresh.generation});await waitFor(()=>expect(v.result.current.collection?.generation).toBe(fresh.generation));await act(async()=>resolve(imported));expect(v.result.current.collection?.generation).toBe(fresh.generation);
});

it('an initial recovery timer never overlaps an explicit descriptor reload',async()=>{
 const server=collection();let resolve!:(value:unknown)=>void;const client={json:vi.fn().mockRejectedValueOnce(new ClientError(503,{message:'offline'} as any)).mockImplementationOnce(()=>new Promise(r=>resolve=r)).mockResolvedValue(server)};
 const v=renderHook(()=>useCountLines(client as any,server.job_id,{generation:server.generation} as any,true,vi.fn()));await waitFor(()=>expect(v.result.current.message).toMatch(/automáticamente/));let reload!:Promise<void>;act(()=>{reload=v.result.current.reload()});await waitFor(()=>expect(client.json).toHaveBeenCalledTimes(2));await new Promise(r=>setTimeout(r,250));expect(client.json).toHaveBeenCalledTimes(2);await act(async()=>{resolve(server);await reload});expect(v.result.current.collection).toEqual(server);v.unmount();
});
