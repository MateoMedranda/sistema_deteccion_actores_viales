import type {CSSProperties} from 'react';
import type {Collection,CountSnapshot,LineWrite} from './countLinesContracts';
import {projectCount} from './countProjection';
import {lineWrites} from './countLinesContracts';
export function CountLineBar({collection,snapshot,position,busy,onChange,selected,onSelect}:{collection?:Collection;snapshot?:CountSnapshot;position:number;busy:boolean;onChange:(lines:LineWrite[])=>Promise<unknown>;selected?:string;onSelect?:(id:string)=>void}){
 if(!collection?.lines.length)return <p className="muted">Sin líneas de conteo. Puedes añadirlas en la sección inferior.</p>;
 const current=snapshot?.generation===collection.generation&&snapshot.revision===collection.revision;
 return <section className="count-line-bar" aria-label="Contadores por línea">{collection.lines.map(line=>{
  const value=current?projectCount(collection,snapshot,line.line_id,position):undefined;
  const ready=value?.status==='ready'&&position>=snapshot!.at_us&&position<value.valid_until_us;
  return <article key={line.line_id} className={"count-line-card"+(selected===line.line_id?" is-selected":"")} style={{'--count-color':line.color} as CSSProperties} data-line-id={line.line_id} data-count-time-us={snapshot?.at_us} data-valid-until-us={value?.valid_until_us}>
   <header><h4>{line.name}</h4><button className="counter-select" aria-pressed={selected===line.line_id} aria-label={"Seleccionar línea "+line.name} onClick={()=>onSelect?.(line.line_id)}>⌖</button></header>
   <div className="counter-value"><strong aria-label={'Cruces en '+line.name}>{ready?value.total:'…'}</strong><span>{ready?(value.result_scope==='final'?'Resultado final':value.result_scope==='partial'?'Resultado parcial':'Cruces confirmados'):value?.status==='unavailable'?(value.error_code==='reanalysis_required'?'Vuelve a analizar el video para contar esta línea.':'No se pudo calcular esta línea; puedes modificarla o iniciar otro análisis.'):'Calculando este tramo…'}</span></div>
   <footer><label><span>Color</span><input type="color" aria-label={'Color de '+line.name} value={line.color} disabled={busy} onChange={e=>{const color=e.target.value.toUpperCase();if(color===line.color.toUpperCase())return;void onChange(lineWrites(collection.lines).map(l=>l.line_id===line.line_id?{...l,color}:l)).catch(()=>{})}}/></label>
   <details className="counter-options"><summary aria-label={'Editar '+line.name}>Editar</summary><label>Nombre<input key={line.name} type="text" aria-label={'Nombre de '+line.name} defaultValue={line.name} disabled={busy} onBlur={e=>{if(e.target.value!==line.name)void onChange(lineWrites(collection.lines).map(l=>l.line_id===line.line_id?{...l,name:e.target.value}:l)).catch(()=>{})}} onKeyDown={e=>{if(e.key==='Enter')e.currentTarget.blur()}}/></label><button className="secondary-button" disabled={busy} aria-label={"Eliminar línea "+line.name} onClick={()=>void onChange(lineWrites(collection.lines).filter(l=>l.line_id!==line.line_id)).catch(()=>{})}>Eliminar línea</button></details></footer>
  </article>;
 })}<p className="muted count-line-note">Cruces por línea en el instante reproducido. Un vehículo puede cruzar varias líneas; estos valores no se suman como vehículos únicos.</p></section>;
}
