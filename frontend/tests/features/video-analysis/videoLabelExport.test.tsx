import {render,screen,fireEvent} from '@testing-library/react';import {it,expect,vi} from 'vitest';import {VideoExport} from '../../../src/features/video-analysis/VideoExport';
it('explicit label export uses the variant receipt and private variant download',async()=>{
 const client={json:vi.fn(async(_path:string)=>({job_id:'v',renderer_version:'vehicle-labels-v1',state:'ready',processed_frames:12,total_frames:12,expires_at:'2099-01-01T00:00:00Z',url:'/api/v1/video-jobs/v/playback/export/content?renderer=vehicle-labels-v1',error_code:null})),labelVideo:vi.fn(()=>'/web-api/label-download')};
 render(<VideoExport client={client as any} id="v" renderer="vehicle-labels-v1" enabled active serverState="waiting" expiresAt="2099-01-01T00:00:00Z" onUnavailable={vi.fn()}/>);
 expect(client.json).not.toHaveBeenCalled();fireEvent.click(screen.getByRole('button',{name:'Exportar video anotado'}));
 expect(await screen.findByRole('link',{name:'Descargar MP4'})).toHaveAttribute('href','/web-api/label-download');expect(client.json.mock.calls[0][0]).toContain('renderer=vehicle-labels-v1');
});
