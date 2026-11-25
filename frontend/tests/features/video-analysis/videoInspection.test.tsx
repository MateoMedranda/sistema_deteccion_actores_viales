import {renderHook,waitFor,act} from '@testing-library/react';
import {it,expect,vi} from 'vitest';
import {inspection010} from '../../fixtures/inspection010';
import {parseInspection} from '../../../src/features/video-analysis/inspectionContracts';
import {ClientError} from '../../../src/services/apiClient';
import {useVideoInspection} from '../../../src/features/video-analysis/useVideoInspection';
it('rejects mismatched contexts and unknown fields',()=>{
 const v=inspection010;expect(parseInspection(v,v.job_id,v.generation,v.track_id,v.frame_index).inspection_id).toBe(v.inspection_id);
 expect(()=>parseInspection({...v,unknown:1},v.job_id,v.generation,v.track_id,v.frame_index)).toThrow();
 expect(()=>parseInspection(v,v.job_id,v.generation,v.track_id,v.frame_index+1)).toThrow();
});
it('reuses the same resolved context and filters late selections',async()=>{
 const v={...inspection010,state:'ready',expires_at:'2099-01-01T00:00:00Z'};let resolve!:(v:unknown)=>void;
 const client={json:vi.fn().mockResolvedValueOnce(v).mockImplementationOnce(()=>new Promise(r=>{resolve=r}))};
 const {result,rerender}=renderHook(({frame})=>useVideoInspection(client as any,v.job_id,{generation:v.generation,track_id:v.track_id,frame_index:frame},vi.fn()),{initialProps:{frame:v.frame_index}});
 await waitFor(()=>expect(result.current.result?.inspection_id).toBe(v.inspection_id));
 rerender({frame:v.frame_index+1});expect(result.current.result).toBeUndefined();
 rerender({frame:v.frame_index});await waitFor(()=>expect(result.current.result?.inspection_id).toBe(v.inspection_id));
 resolve?.({...v,frame_index:v.frame_index+1});expect(result.current.result?.frame_index).toBe(v.frame_index);
});


it('retires expired selection data and distinguishes local expiry from parent expiry',async()=>{
 vi.useFakeTimers();const now=new Date('2026-11-24T12:00:00Z');vi.setSystemTime(now);
 const v={...inspection010,state:'ready',expires_at:new Date(now.getTime()+100).toISOString()};
 const client={json:vi.fn().mockResolvedValue(v)};const unavailable=vi.fn();
 const selection={generation:v.generation,track_id:v.track_id,frame_index:v.frame_index};
 const view=renderHook(()=>useVideoInspection(client as any,v.job_id,selection,unavailable));
 await act(async()=>{await Promise.resolve()});expect(view.result.current.result).toBeDefined();
 await act(async()=>{vi.advanceTimersByTime(110)});expect(view.result.current.result).toBeUndefined();expect(view.result.current.message).toMatch(/vencido/);expect(unavailable).not.toHaveBeenCalled();view.unmount();vi.useRealTimers();
});

it('keeps local 410 in the card and retires a withdrawn parent',async()=>{
 const v=inspection010,unavailable=vi.fn();const client={json:vi.fn().mockRejectedValue(new ClientError(410,{code:'inspection_expired',message:'expired'}))};
 const selection={generation:v.generation,track_id:v.track_id,frame_index:v.frame_index};
 const local=renderHook(()=>useVideoInspection(client as any,v.job_id,selection,unavailable));await waitFor(()=>expect(local.result.current.message).toMatch(/vencido/));expect(unavailable).not.toHaveBeenCalled();local.unmount();
 client.json.mockRejectedValue(new ClientError(410,{code:'artifact_expired',message:'expired'}));renderHook(()=>useVideoInspection(client as any,v.job_id,selection,unavailable));await waitFor(()=>expect(unavailable).toHaveBeenCalledOnce());
});
