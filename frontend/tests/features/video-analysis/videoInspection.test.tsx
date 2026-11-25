import {renderHook,waitFor} from '@testing-library/react';
import {it,expect,vi} from 'vitest';
import {inspection010} from '../../fixtures/inspection010';
import {parseInspection} from '../../../src/features/video-analysis/inspectionContracts';
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
