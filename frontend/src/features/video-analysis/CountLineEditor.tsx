import {useEffect,useState,type RefObject} from 'react';
import {lineWrites,normalizeName,type LineWrite} from './countLinesContracts';
import {ProgressiveCountTools} from './ProgressiveCountTools';
export const DEFAULT_COLORS=['#F59E0B', '#06B6D4', '#EF4444', '#8B5CF6', '#10B981', '#EC4899', '#F97316', '#3B82F6', '#84CC16', '#14B8A6', '#A855F7', '#EAB308', '#0EA5E9', '#F43F5E', '#22C55E', '#D946EF', '#FB923C', '#6366F1', '#A3E635', '#2DD4BF', '#C084FC', '#FACC15', '#38BDF8', '#FB7185', '#4ADE80', '#E879F9', '#EA580C', '#4F46E5', '#65A30D', '#0D9488', '#7C3AED', '#CA8A04'];

type Draft={value:LineWrite;base?:LineWrite;empty?:boolean;conflict?:boolean};
const equal=(a?:LineWrite,b?:LineWrite)=>JSON.stringify(a&&lineFields(a))===JSON.stringify(b&&lineFields(b));
const lineFields=({line_id,name,color,segment}:LineWrite)=>({line_id,name,color,segment});
const nameKey=(name:string)=>{try{return normalizeName(name).toLowerCase()}catch{return name.normalize('NFC').trim().replace(/\s+/gu,' ').toLowerCase()}};
export function CountLineEditor({lines,limit=10,admittedCount,maxAdmittedLines,colors=DEFAULT_COLORS,busy=false,firstFrame,source,pause,position,message,onChange,selectedLine,onSelect}:{lines:LineWrite[];limit?:number;admittedCount?:number;maxAdmittedLines?:number;colors?:string[];busy?:boolean;firstFrame?:HTMLCanvasElement;source:RefObject<HTMLCanvasElement>;pause:()=>void;position:string;message:string;onChange:(lines:LineWrite[])=>Promise<unknown>;selectedLine?:string;onSelect?:(id:string)=>void}){
 const [drafts,setDrafts]=useState<Draft[]>(()=>lines.map(value=>({value,base:value}))),[selected,setSelected]=useState<string|undefined>(lines[0]?.line_id),[error,setError]=useState('');
 // Reconcile each base independently: a readback never erases an unsaved proposal.
 useEffect(()=>{setDrafts(old=>{
  const next:Draft[]=[];
  for(const draft of old){
   const remote=lines.find(l=>l.line_id===draft.value.line_id),dirty=draft.empty||!equal(draft.value,draft.base);
   if(remote&&equal(remote,draft.value)&&!draft.empty){next.push({value:remote,base:remote});continue}
   if(!dirty){if(remote)next.push({value:remote,base:remote});continue}
   next.push({...draft,base:remote,conflict:draft.conflict||!equal(remote,draft.base)});
  }
  for(const value of lines)if(!next.some(d=>d.value.line_id===value.line_id))next.push({value,base:value});
  return next;
 })},[lines]);
 useEffect(()=>{if(selectedLine)setSelected(selectedLine)},[selectedLine]);
 const current=drafts.find(d=>d.value.line_id===selected),line=current?.value;
 const update=(fn:(draft:Draft)=>Draft)=>setDrafts(old=>old.map(d=>d.value.line_id===selected?fn(d):d));
 const newCount=drafts.filter(d=>!d.base&&!d.empty).length;
 const activeCount=lines.length+newCount;
 const admitted=admittedCount??lines.length;
 const admissionFull=maxAdmittedLines!==undefined&&admitted+newCount>=maxAdmittedLines;
 const submit=async(next:LineWrite[])=>{try{const result=await onChange(lineWrites(next));if(result===false)throw Error('El contexto cambió. Revisa el borrador antes de aplicar.');setError('')}catch(e){setError(e instanceof Error?e.message:'No se pudo guardar.');throw e}};
 const add=()=>{
  const color=colors.find(c=>!lines.some(l=>l.color===c)&&!drafts.some(d=>!d.empty&&d.value.color===c));if(!color)return;
  let n=1;while(lines.some(l=>nameKey(l.name)===nameKey(`Línea ${n}`))||drafts.some(d=>nameKey(d.value.name)===nameKey(`Línea ${n}`)))n++;
  const value:LineWrite={line_id:crypto.randomUUID(),name:`Línea ${n}`,color,segment:{point_a:{x:.15,y:.5},point_b:{x:.85,y:.5}}};setDrafts(old=>[...old,{value}]);setSelected(value.line_id);setError('');
 };
 const cancel=()=>{
  const confirmed=lines.find(l=>l.line_id===selected);
  setDrafts(old=>confirmed?old.map(d=>d.value.line_id===selected?{value:confirmed,base:confirmed}:d):old.filter(d=>d.value.line_id!==selected));
  if(!confirmed)setSelected(drafts.find(d=>d.value.line_id!==selected)?.value.line_id);setError('');
 };
 const apply=async(segment:LineWrite['segment'])=>{
  if(!current||!line)return;
  if(current.conflict){setError('Hay un conflicto con la versión confirmada. Revisa o cancela el borrador.');return}
  const value={...line,segment},exists=lines.some(l=>l.line_id===line.line_id);
  const next=exists?lines.map(l=>l.line_id===line.line_id?value:l):[...lines,value];
  await submit(next);
  const canonical=lineWrites([value])[0];update(d=>({...d,value:canonical,base:canonical,empty:false,conflict:false}));
 };
 const remove=async()=>{
  if(!line)return;
  try{await submit(lines.filter(l=>l.line_id!==line.line_id));setDrafts(old=>old.filter(d=>d.value.line_id!==line.line_id));setSelected(drafts.find(d=>d.value.line_id!==line.line_id)?.value.line_id)}catch{}
 };
 return <section className="multiline-editor" aria-label="Configurar líneas de conteo"><header><h3>Líneas de conteo</h3><p className="muted">Pon nombre a cada vía. Dibuja o arrastra sus extremos sobre el primer fotograma y aplica los cambios.</p></header>
 <div className="count-line-tabs">{drafts.map(d=><button type="button" className={selected===d.value.line_id?'is-selected':'secondary-button'} key={d.value.line_id} disabled={busy} aria-pressed={selected===d.value.line_id} onClick={()=>{setSelected(d.value.line_id);onSelect?.(d.value.line_id);setError('')}}><span className="count-color-dot" style={{backgroundColor:d.value.color}}/>{d.value.name||'Borrador sin nombre'}</button>)}<button type="button" disabled={busy||activeCount>=limit||admissionFull} onClick={add}>Añadir línea</button></div>
 <p className="muted">{activeCount} de {limit} líneas activas. Los cambios se confirman al aplicar.</p>
 {maxAdmittedLines!==undefined&&<p className="muted">{admitted} de {maxAdmittedLines} identidades admitidas; las eliminadas también consumen capacidad.{newCount>0?` ${newCount} nuevas propuestas.`:''}{admissionFull?' Se alcanzó el límite de identidades. Puedes editar o eliminar las líneas existentes.':''}</p>}
 {line&&current&&<><div className="count-line-fields"><label>Nombre de la línea<input aria-label="Nombre de la línea" value={line.name} disabled={busy} onChange={e=>update(d=>({...d,value:{...d.value,name:e.target.value}}))}/></label><label>Color de la línea<input aria-label="Color de la línea" type="color" value={line.color} disabled={busy} onChange={e=>update(d=>({...d,value:{...d.value,color:e.target.value.toUpperCase()}}))}/></label></div>
 {current.conflict&&<div role="alert">Conflicto: esta línea cambió en el servidor. Tu borrador se conserva. <button className="secondary-button" disabled={busy||!lines.some(l=>l.line_id===line.line_id)} onClick={()=>{update(d=>({...d,conflict:false}));setError('')}}>Conservar mi borrador sobre la versión actual</button></div>}
 <button className="secondary-button" disabled={busy} onClick={cancel}>Cancelar borrador</button>
 <ProgressiveCountTools key={line.line_id} externallyBusy={busy} firstFrame={firstFrame} source={source} pause={pause} enabled={lines.some(l=>l.line_id===line.line_id)} onDraftChange={segment=>update(d=>({...d,empty:!segment,value:segment?{...d.value,segment}:d.value}))} initialLine={current.empty?undefined:line.segment} color={line.color} otherLines={drafts.filter(d=>!d.empty&&d.value.line_id!==line.line_id).map(d=>d.value)} onApply={apply} onDisable={remove} message={message} position={position}/></>}
 {!line&&<p className="muted">Añade una línea para configurar el conteo opcional.</p>}{error&&<p role="alert">{error}</p>}
 </section>;
}
