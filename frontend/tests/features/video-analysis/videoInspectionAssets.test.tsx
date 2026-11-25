import {render,screen,waitFor} from '@testing-library/react';import {it,expect,vi} from 'vitest';
import {InspectionEvidence} from '../../../src/features/video-analysis/InspectionEvidence';
it('does not reload an unchanged asset after parent polling renders',async()=>{
 vi.stubGlobal('URL',Object.assign(URL,{createObjectURL:vi.fn(()=> 'blob:fixed'),revokeObjectURL:vi.fn()}));
 const client={blob:vi.fn().mockResolvedValue(new Blob(['png']))};const props={client:client as any,path:'/crop',expiry:'2099-01-01T00:00:00Z',label:'Recorte del vehículo'};
 const view=render(<InspectionEvidence {...props}/>);await waitFor(()=>expect(screen.getByRole('img')).toHaveAttribute('src','blob:fixed'));
 view.rerender(<InspectionEvidence {...props}/>);expect(client.blob).toHaveBeenCalledOnce();
});
