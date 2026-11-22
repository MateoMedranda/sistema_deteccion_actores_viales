import {useRef} from "react";
export type WorkspaceMode="image"|"video";
export function WorkspaceTabs({active,onChange}:{active:WorkspaceMode;onChange:(mode:WorkspaceMode)=>void}){
 const refs=useRef<Array<HTMLButtonElement|null>>([]);
 const modes:WorkspaceMode[]=["image","video"];
 return <nav className="workspace-tabs" aria-label="Tipo de análisis"><div role="tablist" aria-label="Imagen o video">{modes.map((mode,index)=><button ref={el=>{refs.current[index]=el;}} key={mode} role="tab" id={"tab-"+mode} aria-controls={"panel-"+mode} aria-selected={active===mode} tabIndex={active===mode?0:-1}
 onKeyDown={e=>{const key=e.key;if(["ArrowRight","ArrowLeft","Home","End"].includes(key)){e.preventDefault();const next=key==="Home"?0:key==="End"?1:1-index;refs.current[next]?.focus();}if(key==="Enter"||key===" "){e.preventDefault();onChange(mode);}}}
 onClick={()=>onChange(mode)}>{mode==="image"?"Imagen":"Video"}</button>)}</div></nav>;
}
