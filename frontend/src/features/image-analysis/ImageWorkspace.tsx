import { useImagePolicy } from "../../hooks/useImagePolicy";
import { ApiClient } from "../../services/apiClient";
import { useImageAnalysis } from "./useImageAnalysis";
import { ImageUpload } from "./ImageUpload";
import { AnalysisProgress } from "./AnalysisProgress";
import { AnnotatedImageViewer } from "./AnnotatedImageViewer";
import { DetectionContext } from "./DetectionContext";
import { ClassLegend } from "./ClassLegend";
import { contextualDetectionId, sceneContextualState } from "./imageAnalysisReducer";
import { DetectionList } from "./DetectionList";
import { VehicleDetails } from "./VehicleDetails";
import "./image-analysis.css";
export function ImageWorkspace({ client }: { client?: ApiClient }) {
  const {
    state,
    selectFile,
    analyze,
    retryEnrichment,
    retryMedia,
    reportMediaFailure,
    resume,
    selectDetection,
    sceneContext,
    rejectEvidence,
    reset,
  } = useImageAnalysis(client);
  const { policy, failed: policyFailed } = useImagePolicy(client);
  const busy = ["detecting", "enriching"].includes(state.phase),
    source = state.response;
  return (
    <section className="image-workspace media-workspace" aria-labelledby="image-heading">
      <div className="workspace-heading">
        <div>
          <span className="eyebrow">ANÁLISIS DE IMÁGENES</span>
          <h2 id="image-heading">De la escena al detalle.</h2>
          <p>Detecta, selecciona y conoce cada vehículo en un solo lugar.</p>
        </div>
        <span className="workspace-tag">Imagen ↗</span>
      </div>
      <ImageUpload
        policy={policy}
        policyFailed={policyFailed}
        compact={!!source}
        disabled={!client || busy || !!source}
        file={state.file}
        preview={state.preview}
        generation={state.generation}
        onChoose={selectFile}
        onAnalyze={() => void analyze()}
        onReset={reset}
      />
      {!client && (
        <p className="connection-note">
          Preparando el análisis automáticamente…
        </p>
      )}
      <AnalysisProgress state={state} />

      {state.warning && <p className="notice">{state.warning}</p>}
      {state.phase === "interrupted" && (
        <button className="secondary" onClick={() => void resume()}>
          Reanudar consulta
        </button>
      )}
      {["failed", "cancelled"].includes(state.phase) && source && (
        <button className="secondary" onClick={() => void retryEnrichment()}>
          Reintentar enriquecimiento
        </button>
      )}
      {source && (
        <div className="exploration-grid">
          <div className="scene-column">
            <div className="scene-heading">
              <h3>Escena analizada</h3>
              <span>
                {source.detections.length} detecciones · {source.image.width} ×{" "}
                {source.image.height}
              </span>
            </div>
            <AnnotatedImageViewer
              source={source}
              url={state.original}
              state={state.originalState}
              onRetry={() => void retryMedia("original")}
              onFailure={() => reportMediaFailure("original")}
              selected={state.selected}
              contextual={sceneContextualState(state)}
              onSelect={selectDetection}
              onContext={sceneContext}
            />
            <DetectionContext source={source} contextual={contextualDetectionId(state)} selected={state.selected}/>
            <ClassLegend source={source}/>
            {state.expiresAt && (
              <p className="muted">
                Imagen y resultados disponibles hasta{" "}
                {new Date(state.expiresAt).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
                . Por privacidad, después se retirarán de esta vista.
              </p>
            )}

            <DetectionList
              source={source}
              selected={state.selected}
              onSelect={selectDetection}
              onContext={sceneContext}
            />
          </div>
          <VehicleDetails
            sourceId={source.request_id}
            client={client} jobId={state.jobId} expiresAt={state.expiresAt} onRejected={rejectEvidence}
            detection={source.detections.find(
              (d) => d.detection_id === state.selected,
            )}
            result={state.selected ? state.results[state.selected] : undefined}
            original={state.original}
            pending={busy}
            onClose={() => selectDetection(undefined)}
          />
        </div>
      )}
      {!source && (
        <div className="workflow-steps">
          <div>
            <b>01</b>
            <h3>Selecciona una imagen</h3>
            <p>Una escena clara es el mejor punto de partida.</p>
          </div>
          <div>
            <b>02</b>
            <h3>Analiza en una acción</h3>
            <p>Detección y enriquecimiento en el mismo flujo.</p>
          </div>
          <div>
            <b>03</b>
            <h3>Explora la evidencia</h3>
            <p>Consulta cada vehículo sin perder el contexto.</p>
          </div>
        </div>
      )}
    </section>
  );
}
