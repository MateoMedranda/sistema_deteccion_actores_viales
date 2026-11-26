import {render,screen,fireEvent,waitFor} from '@testing-library/react';
import {createRef} from 'react';
import {beforeEach,it,expect,vi} from 'vitest';
import {CountLineEditor} from '../../../src/features/video-analysis/CountLineEditor';
import {TEN_LINES} from '../../fixtures/countLines011';
const initial=()=>structuredClone(TEN_LINES.slice(0,2));
beforeEach(()=>{vi.spyOn(HTMLCanvasElement.prototype,'getContext').mockReturnValue({drawImage:vi.fn()} as any)});
function props(lines=initial(),onChange=vi.fn(async(_lines:any[])=>{})){
 return {lines,onChange,firstFrame:document.createElement('canvas'),source:createRef<HTMLCanvasElement>(),pause:vi.fn(),position:'0:00',message:''};
}
it('applying A excludes the unsaved and invalid draft of B',async()=>{
 const p=props();render(<CountLineEditor {...p}/>);
 fireEvent.click(screen.getByRole('button',{name:'VÍA 2'}));fireEvent.change(screen.getByLabelText('Nombre de la línea',{exact:true}),{target:{value:''}});
 fireEvent.click(screen.getByRole('button',{name:'VÍA 1'}));fireEvent.change(screen.getByLabelText('Nombre de la línea',{exact:true}),{target:{value:'A CONFIRMADA'}});
 fireEvent.click(screen.getByRole('button',{name:'Aplicar nueva línea'}));await waitFor(()=>expect(p.onChange).toHaveBeenCalledTimes(1));
 expect(p.onChange.mock.calls[0][0]).toEqual([{...p.lines[0],name:'A CONFIRMADA'},p.lines[1]]);
});
it('deleting A preserves the confirmed B and its local draft separately',async()=>{
 const p=props();render(<CountLineEditor {...p}/>);fireEvent.click(screen.getByRole('button',{name:'VÍA 2'}));fireEvent.change(screen.getByLabelText('Nombre de la línea',{exact:true}),{target:{value:'B PENDIENTE'}});
 fireEvent.click(screen.getByRole('button',{name:'VÍA 1'}));fireEvent.click(screen.getByRole('button',{name:'Desactivar conteo'}));await waitFor(()=>expect(p.onChange).toHaveBeenCalledWith([p.lines[1]]));
 fireEvent.click(screen.getByRole('button',{name:'B PENDIENTE'}));expect(screen.getByLabelText('Nombre de la línea',{exact:true})).toHaveValue('B PENDIENTE');
});
it('uses remote confirmed geometry without resending the old points',async()=>{
 const p=props(),v=render(<CountLineEditor {...p}/>),fresh=structuredClone(p.lines);fresh[0].segment.point_a.y=.8;fresh[0].segment.point_b.y=.8;
 v.rerender(<CountLineEditor {...p} lines={fresh}/>);
 expect(screen.getByLabelText('Punto A vertical')).toHaveValue('0.8');fireEvent.click(screen.getByRole('button',{name:'Aplicar nueva línea'}));await waitFor(()=>expect(p.onChange).toHaveBeenCalled());expect(p.onChange.mock.calls[0][0][0].segment).toEqual(fresh[0].segment);
});
it('retains a dirty draft on reconciliation and requires explicit conflict resolution',async()=>{
 const p=props(),v=render(<CountLineEditor {...p}/>);fireEvent.change(screen.getByLabelText('Nombre de la línea',{exact:true}),{target:{value:'MI BORRADOR'}});
 v.rerender(<CountLineEditor {...p} lines={[{...p.lines[0],name:'OTRA PESTAÑA'},p.lines[1]]}/>);
 expect(screen.getByLabelText('Nombre de la línea',{exact:true})).toHaveValue('MI BORRADOR');expect(screen.getByRole('alert')).toHaveTextContent(/conflicto/i);
 fireEvent.click(screen.getByRole('button',{name:'Aplicar nueva línea'}));expect(p.onChange).not.toHaveBeenCalled();
 await waitFor(()=>expect(screen.getByRole('button',{name:'Aplicar nueva línea'})).toBeEnabled());fireEvent.click(screen.getByRole('button',{name:'Conservar mi borrador sobre la versión actual'}));fireEvent.click(screen.getByRole('button',{name:'Aplicar nueva línea'}));await waitFor(()=>expect(p.onChange).toHaveBeenCalled());
});
it('a cleared new draft never reappears when another line is applied',async()=>{
 const p=props([]);render(<CountLineEditor {...p}/>);fireEvent.click(screen.getByRole('button',{name:'Añadir línea'}));fireEvent.click(screen.getByRole('button',{name:'Borrar línea'}));fireEvent.click(screen.getByRole('button',{name:'Añadir línea'}));fireEvent.click(screen.getByRole('button',{name:'Activar conteo'}));await waitFor(()=>expect(p.onChange).toHaveBeenCalled());expect(p.onChange.mock.calls[0][0]).toHaveLength(1);expect(p.onChange.mock.calls[0][0][0].name).toBe('Línea 2');
});
it.each(['LÍNEA 1','  LÍNEA   1  ','LÍNEA 1'.normalize('NFD')])('proposes a unique default against %s',(name)=>{
 const p=props([{...TEN_LINES[0],name}]);render(<CountLineEditor {...p}/>);fireEvent.click(screen.getByRole('button',{name:'Añadir línea'}));expect(screen.getByLabelText('Nombre de la línea',{exact:true})).toHaveValue('Línea 2');
});
it('announces exhausted accumulated admissions but permits existing metadata and deletion',async()=>{
 const p=props();render(<CountLineEditor {...p} admittedCount={128} maxAdmittedLines={128}/>);expect(screen.getByRole('button',{name:'Añadir línea'})).toBeDisabled();expect(screen.getByText(/128 de 128 identidades/)).toBeVisible();expect(screen.getByRole('button',{name:'Desactivar conteo'})).toBeEnabled();fireEvent.change(screen.getByLabelText('Nombre de la línea',{exact:true}),{target:{value:'RENOMBRADA'}});fireEvent.click(screen.getByRole('button',{name:'Aplicar nueva línea'}));await waitFor(()=>expect(p.onChange).toHaveBeenCalled());
});

it('keyboard geometry edits stay local and a metadata update never resets their points',()=>{
 const p=props(),v=render(<CountLineEditor {...p}/>);fireEvent.keyDown(screen.getByRole('button',{name:'Extremo 1'}),{key:'ArrowDown'});expect(p.onChange).not.toHaveBeenCalled();expect(screen.getByLabelText('Punto A vertical')).toHaveValue('0.11');v.rerender(<CountLineEditor {...p} lines={[{...p.lines[0],color:'#112233'},p.lines[1]]}/>);expect(screen.getByLabelText('Punto A vertical')).toHaveValue('0.11');expect(p.onChange).not.toHaveBeenCalled();
});

it('new defaults avoid confirmed names and colors still held by another dirty draft',()=>{
 const p=props([{...TEN_LINES[0],name:'Línea 1'}]);render(<CountLineEditor {...p}/>);fireEvent.change(screen.getByLabelText('Nombre de la línea',{exact:true}),{target:{value:'BORRADOR'}});fireEvent.change(screen.getByLabelText('Color de la línea'),{target:{value:'#112233'}});fireEvent.click(screen.getByRole('button',{name:'Añadir línea'}));expect(screen.getByLabelText('Nombre de la línea',{exact:true})).toHaveValue('Línea 2');expect(screen.getByLabelText('Color de la línea')).not.toHaveValue(TEN_LINES[0].color.toLowerCase());
});
it('shows the canonical confirmed name after applying a whitespace-normalized draft',async()=>{
 const p=props();render(<CountLineEditor {...p}/>);fireEvent.change(screen.getByLabelText('Nombre de la línea',{exact:true}),{target:{value:'   AV    CENTRAL  '}});fireEvent.click(screen.getByRole('button',{name:'Aplicar nueva línea'}));await waitFor(()=>expect(screen.getByLabelText('Nombre de la línea',{exact:true})).toHaveValue('AV CENTRAL'));expect(p.onChange.mock.calls[0][0][0].name).toBe('AV CENTRAL');
});
