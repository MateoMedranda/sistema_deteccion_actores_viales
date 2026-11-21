import { useMemo, useState } from "react";
import { ApiClient } from "./services/apiClient";
import type { Point } from "./services/apiTypes";
import { normalizeApiUrl } from "./utils/urlValidation";
import { SessionConfig } from "./components/SessionConfig";
import { VideoJobPanel } from "./components/VideoJobPanel";
import { LineEditor } from "./components/LineEditor";
import { CountJobPanel } from "./components/CountJobPanel";
import { EnrichmentPanel } from "./components/EnrichmentPanel";
import { ImageWorkspace } from "./features/image-analysis/ImageWorkspace";
import { useSessionLifecycle } from "./hooks/useSessionLifecycle";
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
  const [videoId, setVideoId] = useState<string>(),
    [preview, setPreview] = useState(""),
    [line, setLine] = useState<[Point, Point]>();
  const lifecycle = useSessionLifecycle(client);
  return (
    <>
      <ImageWorkspace client={client} />
      <details className="legacy-tools">
        <summary>Herramientas de video y conteo</summary>
        <p className="muted">
          Procesa videos y configura una línea de conteo. La exploración
          interactiva de videos llegará en una siguiente iteración.
        </p>
        <VideoJobPanel
          client={client}
          onVideo={setVideoId}
          onPreview={(url) => {
            setPreview(url);
            setLine(undefined);
            setVideoId(undefined);
          }}
          lifecycle={lifecycle}
        />
        {preview && (
          <LineEditor
            key={preview}
            videoUrl={preview}
            onClear={() => setLine(undefined)}
            onLine={(a, b) => setLine([a, b])}
          />
        )}
        <CountJobPanel
          key={"count:" + videoId + ":" + JSON.stringify(line)}
          client={client}
          videoId={videoId}
          line={line}
          lifecycle={lifecycle}
        />
        <EnrichmentPanel
          key={"enrichment:" + videoId}
          client={client}
          videoId={videoId}
          lifecycle={lifecycle}
        />
      </details>
    </>
  );
}
