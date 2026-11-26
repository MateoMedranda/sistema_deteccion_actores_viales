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
