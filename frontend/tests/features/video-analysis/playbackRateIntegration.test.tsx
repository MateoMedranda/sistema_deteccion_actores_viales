import {act,render,screen,fireEvent,waitFor} from '@testing-library/react';
import {beforeEach,afterEach,it,expect,vi} from 'vitest';
import {FrameCache} from '../../../src/features/video-analysis/frameCache';
import fixtures from '../../fixtures/countLines011';
const h=vi.hoisted(()=>({state:undefined as any,latest:{current:undefined as any},cache:{current:undefined as any},ensure:vi.fn(async()=>{}),retire:vi.fn(),wall:1000,raf:new Map<number,FrameRequestCallback>(),seq:0,decoders:[] as any[],inspections:[] as any[],collection:undefined as any,configure:vi.fn(async(_lines:unknown)=>true)}));
vi.mock('../../../src/features/video-analysis/useProgressivePlayback',()=>({useProgressivePlayback:()=>({state:h.state,latest:h.latest,cache:h.cache,ensure:h.ensure,retire:h.retire,message:''})}));
vi.mock('../../../src/features/video-analysis/useCountLines',()=>({useCountLines:()=>({collection:h.collection,message:'',busy:false,configure:h.configure,reload:vi.fn(),importLegacy:vi.fn()})}));
vi.mock('../../../src/features/video-analysis/useDetectionSummary',()=>({useDetectionSummary:()=>undefined}));
vi.mock('../../../src/features/video-analysis/useVideoInspection',()=>({useVideoInspection:(_c:unknown,_id:unknown,selection:unknown)=>{if(selection)h.inspections.push(selection);return {message:'',key:'test'}}}));
vi.mock('../../../src/features/video-analysis/VideoInspectionDetails',()=>({VideoInspectionDetails:()=>null}));
vi.mock('../../../src/features/video-analysis/VideoExport',()=>({VideoExport:()=>null}));
vi.mock('../../../src/features/video-analysis/sourceDecoder',()=>({SourceDecoder:class{
 timeline={rotation:0,config:{codedWidth:640,codedHeight:360},byDisplay:Array.from({length:120},(_,i)=>({sample:{cts:i*100000,timescale:1000000}}))};
 frames=new Map<number,any>();initialize=vi.fn(async()=>{});fill=vi.fn(async()=>{});seek=vi.fn(async()=>{});consume=vi.fn();close=vi.fn();
 constructor(){h.decoders.push(this)}frame(i:number){if(!this.frames.has(i))this.frames.set(i,{timestamp:i*1000,codedWidth:640,codedHeight:360});return this.frames.get(i)}
}}));
import {ProgressiveVideoPlayer} from '../../../src/features/video-analysis/ProgressiveVideoPlayer';
const json=vi.fn(async(path:string)=>{const at=Number(new URL(path,'http://test').searchParams.get('at_us'));return {job_id:h.state.job_id,generation:h.state.generation,protocol:'video-count-lines-v1',policy_version:'finite-center-both-v1',revision:1,at_us:at,available_until_us:h.state.available_until_us,analysis_state:h.state.analysis_state,expires_at:h.state.expires_at,lines:h.collection.lines.map((l:any)=>({line_id:l.line_id,geometry_revision:1,status:'ready',result_scope:'building',covered_until_us:h.state.available_until_us,valid_until_us:Math.min(h.state.available_until_us,at<2000000?2000000:12000000),total:at<2000000?0:1,error_code:null}))}});
const client={json} as any;
async function step(ms=100){await act(async()=>{h.wall+=ms;const callbacks=[...h.raf.values()];h.raf.clear();for(const cb of callbacks)cb(h.wall)})}
const surface=()=>document.querySelector<HTMLCanvasElement>('.progressive-surface canvas')!;
beforeEach(async()=>{
 h.wall=1000;h.seq=0;h.raf.clear();h.decoders=[];h.inspections=[];h.ensure.mockClear();h.configure.mockClear();json.mockClear();
 h.collection=structuredClone(fixtures.valid.find(e=>e.name==='confirmed_collection')!.data);h.collection.expires_at='2099-01-01T00:00:00Z';
 h.state={job_id:h.collection.job_id,generation:h.collection.generation,revision:1,analysis_state:'complete',export_state:'not_requested',frames_published:120,available_until_us:12000000,last_frame_start_us:11900000,media_available:true,source:{size_bytes:1},timeline:{width:640,height:360,duration_us:12000000,duration_confirmed:false},buffer_seconds:.2,expires_at:'2099-01-01T00:00:00Z'};h.latest.current=h.state;
 const cache=new FrameCache();h.cache.current=cache;
 const frames=Array.from({length:120},(_,i)=>({frame_index:i,start_us:i*100000,end_us:(i+1)*100000,pts:String(i),observation_offset:0,observation_total:1,observations:[{ordinal:0,track_id:7,class_id:0,class_name:'Car',confidence:.9,raw_bbox:{x_min:10+i,y_min:20,x_max:60+i,y_max:80},display_bbox:{x_min:10+i,y_min:20,x_max:60+i,y_max:80}}]}));
 await cache.load(h.state,0,12000000,async(cursor)=>({job_id:h.state.job_id,generation:h.state.generation,snapshot:1,from_us:0,to_us:12000000,frames:cursor?frames.slice(100):frames.slice(0,100),next_cursor:cursor?null:'tail'}),new AbortController().signal);
 vi.stubGlobal('VideoDecoder',function(){});vi.stubGlobal('requestAnimationFrame',(cb:FrameRequestCallback)=>{const id=++h.seq;h.raf.set(id,cb);return id});vi.stubGlobal('cancelAnimationFrame',(id:number)=>h.raf.delete(id));vi.spyOn(performance,'now').mockImplementation(()=>h.wall);
 vi.spyOn(HTMLCanvasElement.prototype,'getContext').mockReturnValue(new Proxy({},{get:()=>vi.fn(),set:()=>true}) as any);
});
afterEach(()=>vi.unstubAllGlobals());
it('keeps one decoder, source PTS, boxes, inspection identity and counts across 0.5/1/2x',async()=>{
 const view=render(<ProgressiveVideoPlayer client={client} id={h.state.job_id} active onUnavailable={h.retire}/>);await waitFor(()=>expect(h.decoders).toHaveLength(1));await step();
 const decoder=h.decoders[0],cache=h.cache.current;const results=[];
 for(const rate of [.5,1,2]){
  fireEvent.click(screen.getByRole('button',{name:'Pausar e inspeccionar'}));fireEvent.keyDown(screen.getByRole('slider',{name:/Posición del video/}),{key:'Home'});await step();
  const before=surface().dataset.frameIndex;fireEvent.change(screen.getByRole('combobox',{name:'Velocidad de reproducción'}),{target:{value:String(rate)}});await step(0);expect(surface().dataset.frameIndex).toBe(before);
  fireEvent.click(screen.getByRole('button',{name:/^Reproducir$/}));await step(0);
  for(let i=0;i<10;i++)await step(200/rate);
  fireEvent.click(screen.getByRole('button',{name:'Pausar e inspeccionar'}));await step(0);
  expect(surface().dataset.timeUs).toBe('2000000');expect(surface().dataset.frameIndex).toBe('20');
  fireEvent.click(screen.getByRole('button',{name:'Consultar vehículo 7, Automóvil'}));
  expect(h.inspections.at(-1)).toEqual({generation:h.state.generation,track_id:7,frame_index:20});
  await waitFor(()=>expect(screen.getByLabelText('Cruces en AV SIMÓN BOLIVAR')).toHaveTextContent('1'));
  const hit=document.querySelector<HTMLElement>('.progressive-hitboxes button')!;results.push([surface().dataset.timeUs,hit.style.left,screen.getByLabelText('Cruces en AV SIMÓN BOLIVAR').textContent]);
  expect(h.decoders).toHaveLength(1);expect(h.cache.current).toBe(cache);expect(decoder.frame(20).timestamp).toBe(20000);
 }
 expect(results[1]).toEqual(results[0]);expect(results[2]).toEqual(results[0]);view.unmount();expect(decoder.close).toHaveBeenCalledTimes(1);
});
it('waits at the confirmed prefix at 2x, resumes with that rate, and honors explicit pause',async()=>{
 h.state.analysis_state='analyzing';h.state.available_until_us=1000000;h.state.last_frame_start_us=900000;
 const view=render(<ProgressiveVideoPlayer client={client} id={h.state.job_id} active onUnavailable={h.retire}/>);await step();await step();
 fireEvent.change(screen.getByRole('combobox',{name:'Velocidad de reproducción'}),{target:{value:'2'}});await step(1000);
 expect(Number(surface().dataset.timeUs)).toBeLessThan(1000000);expect(screen.getByText(/Esperando el siguiente tramo analizado/)).toBeVisible();
 h.state={...h.state,available_until_us:4000000,last_frame_start_us:3900000};h.latest.current=h.state;view.rerender(<ProgressiveVideoPlayer client={client} id={h.state.job_id} active onUnavailable={h.retire}/>);await step(0);await step(100);expect(Number(surface().dataset.timeUs)).toBeGreaterThan(900000);
 fireEvent.click(screen.getByRole('button',{name:'Pausar e inspeccionar'}));const paused=surface().dataset.timeUs;await step(500);expect(surface().dataset.timeUs).toBe(paused);expect(screen.getByRole('combobox',{name:'Velocidad de reproducción'})).toHaveValue('2');expect(h.decoders).toHaveLength(1);
});

it('does not silently mark a different initial draft as applied',async()=>{
 const draft={lines:[{...h.collection.lines[0],name:'BORRADOR INICIAL'}]};
 render(<ProgressiveVideoPlayer client={client} id={h.state.job_id} active onUnavailable={h.retire} countDraft={draft}/>);
 await waitFor(()=>expect(screen.getByRole('alert')).toHaveTextContent(/distintas del borrador inicial/));expect(h.configure).not.toHaveBeenCalled();
 fireEvent.click(screen.getByRole('button',{name:'Aplicar borrador inicial sobre la versión actual'}));await waitFor(()=>expect(h.configure).toHaveBeenCalledWith(draft.lines));await waitFor(()=>expect(screen.queryByRole('alert')).not.toBeInTheDocument());
});
