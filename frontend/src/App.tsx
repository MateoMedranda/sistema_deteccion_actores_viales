import { useState } from "react";
import type { ApiClient } from "./services/apiClient";
import { WorkspaceTabs, type WorkspaceMode } from "./components/WorkspaceTabs";
import { ImageWorkspace } from "./features/image-analysis/ImageWorkspace";
import { VideoWorkspace } from "./features/video-analysis/VideoWorkspace";
import { useManagedSession } from "./hooks/useManagedSession";

export default function App() {
    const connection = useManagedSession(), [mode, setMode] = useState<WorkspaceMode>("image");
    return <main data-session-state={connection.state}>
        <header className="app-header">
            <div className="brand"><div className="brand-mark" aria-hidden="true">V</div><div><h1>Observatorio Vial</h1><p>Inteligencia visual · Análisis de vehículos</p></div></div>
            <WorkspaceTabs active={mode} onChange={setMode} />
            <div className="header-actions">
                <span className="session-badge">Sesión privada</span>
                <button className="session-reset" aria-label="Reiniciar sesión" title="Borrar resultados y reiniciar sesión" disabled={connection.state !== "ready"} onClick={() => void connection.reset()}>
                    <span aria-hidden="true">↺</span>
                </button>
            </div>
        </header>
        <span className="sr-only" role="status">{connection.state === "ready" ? "Servicio conectado" : "Preparando el análisis. Recuperando la conexión automáticamente."}</span>
        <SessionContent key={connection.session?.epoch ?? "disconnected"} client={connection.client} mode={mode} />
        <footer className="app-footer">Archivos y resultados temporales · El análisis depende de la calidad de la fuente</footer>
    </main>;
}

function SessionContent({ client, mode }: { client?: ApiClient; mode: WorkspaceMode }) {
    return (
        <>
            <div id="panel-image" role="tabpanel" aria-labelledby="tab-image" hidden={mode !== "image"}>
                <ImageWorkspace client={client} />
            </div>
            <div id="panel-video" role="tabpanel" aria-labelledby="tab-video" hidden={mode !== "video"}>
                <VideoWorkspace client={client} active={mode === "video"} />
            </div>
        </>
    );
}
