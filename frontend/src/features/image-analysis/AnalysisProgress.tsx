import type { ImageState } from "./imageAnalysisReducer";
const labels = {
  cancelled: "Enriquecimiento cancelado",
  idle: "Preparado",
  ready: "Imagen seleccionada",
  detecting: "Detectando actores",
  enriching: "Enriqueciendo vehículos",
  completed: "Análisis completo",
  partial: "Resultado parcial",
  empty: "Sin vehículos elegibles",
  failed: "Requiere atención",
  interrupted: "Consulta interrumpida",
  expired: "Evidencia vencida",
};
export function AnalysisProgress({ state }: { state: ImageState }) {
  const busy = ["detecting", "enriching"].includes(state.phase);
  const measured =
    !!state.jobId &&
    ["queued", "processing"].includes(state.enrichmentStage ?? "");
  const stageLabels = {
    submitting: "Enviando enriquecimiento",
    queued: "En cola",
    processing: "Procesando vehículos",
  };
  const title =
    state.phase === "enriching" &&
    state.enrichmentStage &&
    state.enrichmentStage in stageLabels
      ? stageLabels[state.enrichmentStage as keyof typeof stageLabels]
      : labels[state.phase];
  return (
    <div
      className={"analysis-status status-" + state.phase}
      role="status"
      aria-live="polite"
    >
      <span
        className={"status-dot " + (busy ? "is-busy" : "")}
        aria-hidden="true"
      />
      <div>
        <strong>{title}</strong>
        <p>{state.message || "Selecciona una imagen para empezar."}</p>
        {busy && (
          <progress
            aria-label="Progreso del enriquecimiento"
            max={100}
            value={measured ? state.progress : undefined}
          />
        )}
      </div>
      {busy && (
        <span className="progress-number">
          {measured ? Math.round(state.progress) + "%" : "En curso"}
        </span>
      )}
    </div>
  );
}
