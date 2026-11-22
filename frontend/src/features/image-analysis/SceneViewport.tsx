import {useEffect,useLayoutEffect,useRef,useState,type ReactNode} from "react";
import {fitScale,normalizedAnchor,scrollForAnchor,validScale,type Anchor} from "./sceneViewportGeometry";
type Drag={id:number;x:number;y:number;left:number;top:number;dragged:boolean};
export function SceneViewport({sourceId,width,height,children}:{sourceId:string;width:number;height:number;children:ReactNode}){
 const root=useRef<HTMLDivElement>(null),viewport=useRef<HTMLDivElement>(null);
 const [mode,setMode]=useState<"fit"|"intrinsic">("fit"),[intrinsic,setIntrinsic]=useState(1);
 const [size,setSize]=useState({width:0,height:0}),anchor=useRef<Anchor>({x:.5,y:.5});
 const drag=useRef<Drag>(),suppress=useRef(false),suppressionTimer=useRef<ReturnType<typeof setTimeout>>();
 const fit=fitScale(width,height,size.width,size.height),scale=mode==="fit"?fit:Math.max(fit,intrinsic);
 const remember=()=>{const v=viewport.current;if(v&&v.clientWidth&&v.clientHeight)anchor.current=normalizedAnchor(v.scrollLeft,v.scrollTop,v.clientWidth,v.clientHeight,width*scale,height*scale);};
 const release=()=>{const d=drag.current,v=viewport.current;if(d&&v?.hasPointerCapture?.(d.id))v.releasePointerCapture(d.id);drag.current=undefined;};
 useLayoutEffect(()=>{setMode("fit");setIntrinsic(1);anchor.current={x:.5,y:.5};suppress.current=false;release();},[sourceId,width,height]);
 useLayoutEffect(()=>{
  const measure=()=>{const w=root.current?.clientWidth??0;if(w>0)setSize(old=>{const h=Math.min(window.innerHeight*.7,720);return old.width===w&&old.height===h?old:{width:w,height:h};});};
  measure();const observer=typeof ResizeObserver!=="undefined"?new ResizeObserver(measure):undefined;
  if(root.current)observer?.observe(root.current);window.addEventListener("resize",measure);
  return()=>{observer?.disconnect();window.removeEventListener("resize",measure);};
 },[]);
 useLayoutEffect(()=>{const v=viewport.current;if(!v||!v.clientWidth||!v.clientHeight)return;const p=scrollForAnchor(anchor.current,v.clientWidth,v.clientHeight,width*scale,height*scale);v.scrollLeft=p.left;v.scrollTop=p.top;},[scale,width,height,size]);
 useEffect(()=>{window.addEventListener("blur",release);return()=>{window.removeEventListener("blur",release);release();if(suppressionTimer.current)clearTimeout(suppressionTimer.current);};},[]);
 const zoom=(value:number|"fit")=>{remember();if(value==="fit"){anchor.current={x:.5,y:.5};setMode("fit");}else if(validScale(value)){const bounded=Math.max(fit,value);setIntrinsic(bounded);setMode(bounded<=fit?"fit":"intrinsic");}};
 const finish=(cancel=false)=>{if(drag.current?.dragged&&!cancel){suppress.current=true;if(suppressionTimer.current)clearTimeout(suppressionTimer.current);suppressionTimer.current=setTimeout(()=>{suppress.current=false;},0);}release();};
 return <div ref={root} className="scene-viewport">
 <div className="scene-toolbar" role="group" aria-label="Zoom de la escena">
 <button onClick={()=>zoom("fit")} aria-pressed={mode==="fit"}>Ajustar</button>
 {[1,2,4].map(n=><button key={n} aria-pressed={mode==="intrinsic"&&intrinsic===n} onClick={()=>zoom(n)}>{n*100}%</button>)}
 <button aria-label="Alejar imagen" disabled={scale<=fit+1e-8} onClick={()=>zoom(Math.max(fit,scale/1.5))}>−</button>
 <button aria-label="Acercar imagen" onClick={()=>zoom(Math.min(4,scale*1.5))}>+</button>
 <button onClick={()=>zoom("fit")}>Restablecer</button><output aria-live="polite">{Math.round(scale*100)}%</output>
 </div>
 <div ref={viewport} className="scene-scrollport" role="region" aria-label="Explorar escena original" tabIndex={0}
 style={{height:size.width?Math.min(height*fit,size.height):undefined,touchAction:mode==="fit"?"pan-y":"none"}}
 onScroll={remember} onKeyDown={e=>{if(e.target!==e.currentTarget)return;const v=e.currentTarget,step=e.shiftKey?120:40;if(e.key==="Home"){e.preventDefault();v.scrollLeft=0;v.scrollTop=0;}else if(["ArrowLeft","ArrowRight","ArrowUp","ArrowDown"].includes(e.key)){e.preventDefault();v.scrollLeft+=e.key==="ArrowLeft"?-step:e.key==="ArrowRight"?step:0;v.scrollTop+=e.key==="ArrowUp"?-step:e.key==="ArrowDown"?step:0;}}}
 onPointerDown={e=>{if(e.button!==0||mode==="fit")return;suppress.current=false;const v=e.currentTarget;drag.current={id:e.pointerId,x:e.clientX,y:e.clientY,left:v.scrollLeft,top:v.scrollTop,dragged:false};}}
 onPointerMove={e=>{const d=drag.current;if(!d||d.id!==e.pointerId)return;const dx=e.clientX-d.x,dy=e.clientY-d.y;if(!d.dragged&&Math.hypot(dx,dy)>=6){d.dragged=true;e.currentTarget.setPointerCapture?.(e.pointerId);}if(d.dragged){e.preventDefault();e.currentTarget.scrollLeft=d.left-dx;e.currentTarget.scrollTop=d.top-dy;}}}
 onPointerUp={()=>finish()} onPointerCancel={()=>finish(true)}
 onClickCapture={e=>{if(suppress.current){e.preventDefault();e.stopPropagation();suppress.current=false;}}}>
 <div className="scene-viewer scene-stage" data-testid="scene-stage" data-scale={scale} style={{width:width*scale,height:height*scale}}>{children}</div>
 </div><p className="scene-help">Amplía para explorar. Arrastra la escena o usa las flechas con el visor enfocado.</p>
 </div>;
}
