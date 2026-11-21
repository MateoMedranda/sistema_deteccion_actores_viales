import type { Detection, VehicleResult } from "../../services/apiTypes";
import { ApiClient } from "../../services/apiClient";
import { PlateComparison } from "./PlateComparison";
import { classPresentation } from "./classPresentation";
import { EvidenceCrop } from "./EvidenceCrop";
const plateLabels = {
  read: "Placa leída",
  unreadable: "Placa ilegible",
  not_detected: "Placa no detectada",
  failed: "Lectura no disponible",
};
export function VehicleDetails({
  sourceId,
  client,jobId,expiresAt,onRejected,
  detection,
  result,
  original,
  pending,
  onClose,
}: {
  sourceId: string;
  client?:ApiClient;jobId?:string;expiresAt?:number;onRejected?:(error:unknown)=>void;
  detection?: Detection;
  result?: VehicleResult;
  original: string;
  pending: boolean;
  onClose: () => void;
}) {
  return (
    <aside
      id="vehicle-details"
      className="vehicle-details"
      aria-label="Ficha del vehículo"
    >
      {!detection ? (
        <div className="details-empty">
          <span aria-hidden="true">⌖</span>
          <h3>Explora cada vehículo</h3>
          <p>
            Selecciona un recuadro de la imagen o un vehículo de la lista para
            ver su evidencia y sus datos.
          </p>
        </div>
      ) : (
        <>
          <div className="details-heading">
            <div>
              <span className="eyebrow">FICHA DEL VEHÍCULO</span>
              <h3>Detección {detection.detection_id}</h3>
            </div>
            <button
              className="icon-button"
              aria-label="Cerrar ficha del vehículo"
              onClick={onClose}
            >
              ×
            </button>
          </div>
          <div className="vehicle-meta">
            <span><i className="class-swatch" style={{backgroundColor:classPresentation(detection.class_name).color}} aria-hidden="true"/>{classPresentation(detection.class_name).label}</span>
            <span>{Math.round(detection.confidence * 100)}% de confianza</span>
          </div>
          <EvidenceCrop
            original={original}
            box={detection.bbox}
            label="Recorte del vehículo"
            identity={sourceId + ":" + detection.detection_id + ":vehicle"}
          />
          <div className="detail-section">
            <h4>Atributos</h4>
            {!result ? (
              <p className="muted">
                {pending
                  ? "Consultando atributos…"
                  : "Atributos no disponibles."}
              </p>
            ) : result.attributes_status === "failed" ? (
              <p className="muted">No se pudieron consultar los atributos.</p>
            ) : result.attributes.length ? (
              <dl className="attribute-list">
                {result.attributes.map((a) => (
                  <div key={a.name}>
                    <dt>
                      {(
                        {
                          color: "Color",
                          make: "Marca",
                          model: "Modelo",
                          type: "Tipo",
                        } as Record<string, string>
                      )[a.name] ?? a.name}
                    </dt>
                    <dd>
                      {a.label}
                      <small>{Math.round(a.confidence * 100)}%</small>
                    </dd>
                  </div>
                ))}
              </dl>
            ) : (
              <p className="muted">Sin atributos disponibles.</p>
            )}
          </div>
          <div className="detail-section">
            <h4>Placa</h4>
            <span
              className={
                "plate-status plate-" + (result?.plate.status ?? "pending")
              }
            >
              {result
                ? plateLabels[result.plate.status]
                : pending
                  ? "Consultando placa…"
                  : "Placa no disponible"}
            </span>
            {result?.plate.status === "read" && result.plate.text && (
              <div className="plate-text">{result.plate.text}</div>
            )}
            <PlateComparison key={sourceId+":"+jobId+":"+detection.detection_id} client={client} jobId={jobId} sourceId={sourceId} detection={detection} result={result} original={original} expiresAt={expiresAt} onRejected={onRejected}/>
            {result?.plate.ocr_confidence !== undefined && (
              <p className="confidence-note">
                Confianza de lectura:{" "}
                {Math.round(result.plate.ocr_confidence * 100)}%
              </p>
            )}
          </div>
          <p className="privacy-note">
            Imagen estática · Identificador de detección local a esta imagen.
          </p>
        </>
      )}
    </aside>
  );
}
