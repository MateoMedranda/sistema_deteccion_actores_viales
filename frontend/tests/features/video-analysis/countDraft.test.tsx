import {renderHook,act,waitFor} from '@testing-library/react';import {it,expect,vi} from 'vitest';
import {useCountDraft} from '../../../src/features/video-analysis/useCountDraft';
it('captures first local frame without uploading, revokes URL and drops draft when replacing file',async()=>{
 const original=document.createElement.bind(document);let video!:HTMLVideoElement;
 vi.spyOn(document,'createElement').mockImplementation(((name:string,...args:any[])=>{const element=original(name,...args);if(name==='video'){video=element as HTMLVideoElement;Object.defineProperties(video,{videoWidth:{value:640},videoHeight:{value:360}});vi.spyOn(video,'pause').mockImplementation(()=>{});vi.spyOn(video,'load').mockImplementation(()=>{})}return element}) as any);
 vi.spyOn(HTMLCanvasElement.prototype,'getContext').mockReturnValue({drawImage:vi.fn()} as any);
 const revoke=vi.fn();vi.stubGlobal('URL',Object.assign(URL,{createObjectURL:vi.fn(()=>'blob:local'),revokeObjectURL:revoke}));
 const {result,rerender}=renderHook(({file})=>useCountDraft(file),{initialProps:{file:new File(['synthetic'],'one.mp4',{type:'video/mp4'})}});
 act(()=>video.onloadeddata?.(new Event('loadeddata')));await waitFor(()=>expect(result.current.firstFrame?.width).toBe(640));
 act(()=>result.current.setDraft({lines:[{line_id:'22222222-2222-4222-8222-222222222222',name:'Ruta',color:'#F59E0B',segment:{point_a:{x:.1,y:.5},point_b:{x:.9,y:.5}}}]}));
 rerender({file:new File(['next'],'two.mp4',{type:'video/mp4'})});expect(result.current.draft).toBeUndefined();expect(revoke).toHaveBeenCalledWith('blob:local');
});
