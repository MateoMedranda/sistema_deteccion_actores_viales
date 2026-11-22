import { useMemo, useState } from "react";
import { ApiClient } from "./services/apiClient";
import { normalizeApiUrl } from "./utils/urlValidation";
import { SessionConfig } from "./components/SessionConfig";
import { WorkspaceTabs } from "./components/WorkspaceTabs";
import { VideoWorkspace } from "./features/video-analysis/VideoWorkspace";
import { ImageWorkspace } from "./features/image-analysis/ImageWorkspace";
const initialUrl = "http://127.0.0.1:8000";
export default function App() {
  const [baseUrl, setBaseUrl] = useState(initialUrl),
    [apiKey, setApiKey] = useState(""),
    [generation, setGeneration] = useState(0),
    [message, setMessage] = useState("");
  const client = useMemo(() => {
    try {
      return apiKey
        ? new ApiClient(normalizeApiUrl(baseUrl), apiKey)
        : undefined;
    } catch {
      return undefined;
    }
  }, [baseUrl, apiKey]);
  const changeBase = (v: string) => {
      setBaseUrl(v);
      setGeneration((g) => g + 1);
    },
    changeKey = (v: string) => {
      setApiKey(v);
      setGeneration((g) => g + 1);
    };
  const reset = () => {
    setApiKey("");
    setBaseUrl(initialUrl);
    setGeneration((g) => g + 1);
    setMessage("Sesión reiniciada.");
  };
  return (
    <main>
      <header className="app-header">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">
            V
          </div>
          <div>
            <h1>Observatorio Vial</h1>
            <p>Inteligencia visual · Análisis de vehículos</p>
          </div>
        </div>
        <span className="session-badge">
          {client ? "Sesión configurada" : "Sesión privada"}
        </span>
      </header>
      <SessionConfig
        baseUrl={baseUrl}
        apiKey={apiKey}
        onBaseUrl={changeBase}
        onApiKey={changeKey}
        onReset={reset}
      />
      {message && (
        <p className="app-message" role="status">
          {message}
        </p>
      )}
      <SessionContent key={generation} client={client} />
      <footer className="app-footer">
        Evidencia temporal · Resultados sujetos a la calidad de la imagen
      </footer>
    </main>
  );
}
function SessionContent({ client }: { client?: ApiClient }) {
 const [mode,setMode]=useState<"image"|"video">("image");
 return <><WorkspaceTabs active={mode} onChange={setMode}/>
 <div id="panel-image" role="tabpanel" aria-labelledby="tab-image" hidden={mode!=="image"}><ImageWorkspace client={client}/></div>
 <div id="panel-video" role="tabpanel" aria-labelledby="tab-video" hidden={mode!=="video"}><VideoWorkspace client={client} active={mode==="video"}/></div></>;
}
