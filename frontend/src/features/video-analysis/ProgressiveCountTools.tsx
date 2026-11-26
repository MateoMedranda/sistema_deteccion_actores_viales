import {type CountDirection} from "./directionArrow";
import {useEffect,useRef,useState,type RefObject,type PointerEvent} from "react";
import type {CountLine,Point} from "./useProgressiveCount";
type Drag={kind:"point"|"line";index:number;start:Point;initial:Point[]};
const clamp=(n:number)=>Math.max(0,Math.min(1,n));
export function ProgressiveCountTools({firstFrame,source,pause,enabled,onApply,onDisable,message,position,initialLine,initialDirection,color="#F59E0B",otherLines=[],externallyBusy=false,onDraftChange}:{firstFrame?:HTMLCanvasElement;source:RefObject<HTMLCanvasElement>;pause:()=>void;enabled:boolean;onApply:(line:CountLine,direction?:CountDirection)=>Promise<void>;onDisable:()=>Promise<void>;message:string;position:string;initialLine?:CountLine;initialDirection?:CountDirection;color?:string;externallyBusy?:boolean;otherLines?:Array<{line_id:string;color:string;segment:CountLine}>;onDraftChange?:(segment:CountLine)=>void}){
 const editor=useRef<HTMLCanvasElement>(null),area=useRef<HTMLDivElement>(null),drag=useRef<Drag>();
 const [prepared,setPrepared]=useState(false),[points,setPoints]=useState<Point[]>(initialLine?[initialLine.point_a,initialLine.point_b]:[]),[busy,setBusy]=useState(false),[capturedAt,setCapturedAt]=useState("0:00");

 const copy=(image:HTMLCanvasElement)=>{const c=editor.current;if(!c)return;c.width=image.width;c.height=image.height;c.getContext("2d")?.drawImage(image,0,0);setPrepared(true)};
 useEffect(()=>{if(firstFrame){copy(firstFrame);setCapturedAt("0:00")}},[firstFrame]);
 const capture=()=>{pause();const original=source.current;if(!original||original.dataset.frameIndex===undefined)return;copy(original);setCapturedAt(position)};
 const point=(e:PointerEvent<HTMLDivElement>)=>{const b=e.currentTarget.getBoundingClientRect();return {x:clamp((e.clientX-b.left)/b.width),y:clamp((e.clientY-b.top)/b.height)}};
 const down=(e:PointerEvent<HTMLDivElement>)=>{
  if(!prepared||busy||externallyBusy||e.button!==0)return;e.preventDefault();e.currentTarget.setPointerCapture(e.pointerId);
  const start=point(e),button=(e.target as Element).closest<HTMLButtonElement>("[data-endpoint]");
  if(button){drag.current={kind:"point",index:Number(button.dataset.endpoint),start,initial:points};return}
  if(points.length===2){
   const rect=e.currentTarget.getBoundingClientRect(),a=points[0],b=points[1],vx=(b.x-a.x)*rect.width,vy=(b.y-a.y)*rect.height;
   const wx=(start.x-a.x)*rect.width,wy=(start.y-a.y)*rect.height,length=vx*vx+vy*vy,t=length?clamp((wx*vx+wy*vy)/length):0;
   if(length&&Math.hypot(wx-t*vx,wy-t*vy)<=14){drag.current={kind:"line",index:0,start,initial:points};return}
   if(a.x===b.x&&a.y===b.y){const next=[a,start];setPoints(next);drag.current={kind:"point",index:1,start,initial:next};return}
  }
  const next=[start,start];setPoints(next);drag.current={kind:"point",index:1,start,initial:next};
 };
 const move=(e:PointerEvent<HTMLDivElement>)=>{
  const d=drag.current;if(!d)return;const current=point(e);
  if(d.kind==="line"){
   const dx=Math.max(-Math.min(...d.initial.map(p=>p.x)),Math.min(1-Math.max(...d.initial.map(p=>p.x)),current.x-d.start.x));
   const dy=Math.max(-Math.min(...d.initial.map(p=>p.y)),Math.min(1-Math.max(...d.initial.map(p=>p.y)),current.y-d.start.y));
   setPoints(d.initial.map(p=>({x:p.x+dx,y:p.y+dy})));
  }else setPoints(old=>old.map((p,i)=>i===d.index?current:p));
 };
 const end=(e:PointerEvent<HTMLDivElement>)=>{drag.current=undefined;if(e.currentTarget.hasPointerCapture?.(e.pointerId))e.currentTarget.releasePointerCapture(e.pointerId)};
 const apply=async()=>{if(points.length!==2)return;setBusy(true);try{await onApply({point_a:points[0],point_b:points[1]})}catch{}finally{setBusy(false)}};
 useEffect(()=>{if(points.length===2)onDraftChange?.({point_a:points[0],point_b:points[1]})},[points]);
 const valid=points.length===2&&(points[0].x!==points[1].x||points[0].y!==points[1].y);
 return <section className="progressive-count-tools" aria-label="Conteo por línea">
 <div className="count-tools-heading"><div><span className="eyebrow">CONTEO OPCIONAL</span><h3>Línea de conteo</h3><p className="muted">En el primer fotograma, pulsa y arrastra para dibujar. Arrastra los extremos amarillos o el centro de la línea para ajustarla.</p></div>{enabled&&<button className="secondary-button" onClick={()=>void onDisable()} disabled={externallyBusy||busy}>Desactivar conteo</button>}</div>
 {!prepared&&<p role="status">Preparando el primer fotograma analizado…</p>}
 <div ref={area} className={"count-frame-editor"+(prepared?" is-prepared":"")} hidden={!prepared} onPointerDown={down} onPointerMove={move} onPointerUp={end} onPointerCancel={end} onLostPointerCapture={()=>{drag.current=undefined}}>
 <canvas ref={editor} aria-label="Primer fotograma para configurar la línea de conteo"/>
 <svg viewBox="0 0 1 1" preserveAspectRatio="none" aria-hidden="true">{otherLines.map(l=><line key={l.line_id} x1={l.segment.point_a.x} y1={l.segment.point_a.y} x2={l.segment.point_b.x} y2={l.segment.point_b.y} style={{stroke:l.color,opacity:.65}}/>)}{valid&&<line x1={points[0].x} y1={points[0].y} x2={points[1].x} y2={points[1].y} style={{stroke:color}}/>}</svg>
 {points.map((p,i)=><button key={i} type="button" data-endpoint={i} className="line-handle count-line-handle" aria-label={"Extremo "+(i+1)} style={{left:p.x*100+"%",top:p.y*100+"%"}} onKeyDown={e=>{const delta:Record<string,Point>={ArrowLeft:{x:-1,y:0},ArrowRight:{x:1,y:0},ArrowUp:{x:0,y:-1},ArrowDown:{x:0,y:1}};const v=delta[e.key];if(!v)return;e.preventDefault();e.stopPropagation();const step=e.shiftKey?.05:.01;setPoints(old=>old.map((n,j)=>i===j?{x:clamp(n.x+v.x*step),y:clamp(n.y+v.y*step)}:n))}}/>)}</div>
 {prepared&&<><p className="muted">Cuenta los vehículos que atraviesan el segmento en cualquiera de los dos sentidos. Cada identidad suma una vez por línea.</p><p className="muted">Fotograma de {capturedAt}. El contador del video principal sigue el instante que reproduces.</p><div className="count-editor-actions"><button disabled={externallyBusy||busy||!valid} onClick={()=>void apply()}>{busy?"Activando conteo…":enabled?"Aplicar nueva línea":"Activar conteo"}</button><button className="secondary-button" disabled={externallyBusy||busy||!points.length} onClick={()=>{setPoints([]);drag.current=undefined;if(enabled)void onDisable()}}>Borrar línea</button></div>
 <details className="count-advanced"><summary>Opciones de ajuste</summary><button className="secondary-button" onClick={()=>{if(firstFrame){copy(firstFrame);setCapturedAt("0:00")}}}>Volver al primer fotograma</button><button className="secondary-button" onClick={capture} disabled={externallyBusy||busy}>Usar fotograma actual para la línea</button><button className="secondary-button" onClick={()=>setPoints([{x:.15,y:.5},{x:.85,y:.5}])}>Crear línea horizontal</button><div className="count-coordinate-fields">{points.map((p,i)=><fieldset key={i}><legend>Punto {i===0?"A":"B"}</legend>{(["x","y"] as const).map(axis=><label key={axis}>{axis==="x"?"Horizontal":"Vertical"}<input type="range" min="0" max="1" step="0.01" aria-label={"Punto "+(i===0?"A":"B")+" "+(axis==="x"?"horizontal":"vertical")} value={p[axis]} onChange={e=>{const n=Number(e.target.value);setPoints(old=>old.map((v,j)=>j===i?{...v,[axis]:n}:v))}}/></label>)}</fieldset>)}</div></details></>}
 {message&&<p role="status">{message}</p>}</section>;
}
