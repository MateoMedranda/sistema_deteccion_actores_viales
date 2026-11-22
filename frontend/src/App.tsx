import {useState} from "react";
import type {ApiClient} from "./services/apiClient";
import {WorkspaceTabs} from "./components/WorkspaceTabs";
import {ConnectionStatus} from "./components/ConnectionStatus";
import {ImageWorkspace} from "./features/image-analysis/ImageWorkspace";
import {VideoWorkspace} from "./features/video-analysis/VideoWorkspace";
import {useManagedSession} from "./hooks/useManagedSession";
export default function App(){
 const connection=useManagedSession();
 return <main><header className="app-header"><div className="brand"><div className="brand-mark" aria-hidden="true">V</div><div><h1>Observatorio Vial</h1><p>Inteligencia visual · Análisis de vehículos</p></div></div><span className="session-badge">Sesión privada</span></header>
 <ConnectionStatus state={connection.state} onRetry={()=>void connection.connect()} onReset={()=>void connection.reset()}/>
 <SessionContent key={connection.session?.epoch??"disconnected"} client={connection.client}/>
 <footer className="app-footer">Evidencia temporal · Resultados sujetos a la calidad de la fuente</footer></main>;
}
function SessionContent({client}:{client?:ApiClient}){
 const [mode,setMode]=useState<"image"|"video">("image");
 return <><WorkspaceTabs active={mode} onChange={setMode}/><div id="panel-image" role="tabpanel" aria-labelledby="tab-image" hidden={mode!=="image"}><ImageWorkspace client={client}/></div><div id="panel-video" role="tabpanel" aria-labelledby="tab-video" hidden={mode!=="video"}><VideoWorkspace client={client} active={mode==="video"}/></div></>;
}
