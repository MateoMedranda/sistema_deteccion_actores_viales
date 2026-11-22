import type { ImagePolicy } from "../../services/apiTypes";
import { useId } from "react";
export function ImageUpload({
  disabled,
  file,
  preview,
  generation,
  onChoose,
  onAnalyze,
  onReset,
  compact,
  policy,
  policyFailed,
}: {
  policy?: ImagePolicy;
  policyFailed?: boolean;
  compact?: boolean;
  disabled: boolean;
  file?: File;
  preview: string;
  generation: number;
  onChoose: (f?: File) => void;
  onAnalyze: () => void;
  onReset: () => void;
}) {
  const id = useId();
  return (
    <div className={"upload-card " + (compact ? "is-compact" : "")}>
      <div className="upload-icon" aria-hidden="true">
        ↥
      </div>
      <div className="upload-copy">
        <h3>Tu imagen, lista para explorar</h3>
        <p>
          Sube una escena vial. Detectaremos los vehículos y consultaremos sus
          atributos y placas automáticamente.
        </p>
        <label className="file-label" htmlFor={id}>
          Seleccionar imagen
          <input
            key={generation}
            id={id}
            aria-label="Seleccionar imagen"
            type="file"
            accept="image/jpeg,image/png"
            onChange={(e) => onChoose(e.target.files?.[0])}
          />
        </label>
        <small>JPEG o PNG · Archivos temporales y privados</small>
        <small>
          {policy
            ? `Máximo ${new Intl.NumberFormat("es", { maximumFractionDigits: 2 }).format(policy.max_upload_bytes / 1024 / 1024)} MiB y ${new Intl.NumberFormat("es", { maximumFractionDigits: 2 }).format(policy.max_image_pixels / 1000000)} MP (${policy.max_image_pixels.toLocaleString("es")} píxeles).`
            : policyFailed
              ? "No se pudieron consultar los límites; el servicio validará el archivo."
              : "Preparando los límites de carga automáticamente…"}
        </small>
      </div>
      {preview && (
        <img
          className="upload-preview"
          src={preview}
          alt="Vista previa de la imagen seleccionada"
        />
      )}
      <div className="upload-actions">
        <span className="filename">
          {file?.name ?? "Ningún archivo seleccionado"}
        </span>
        <button
          className="primary"
          disabled={disabled || !file}
          onClick={onAnalyze}
        >
          Analizar imagen <span aria-hidden="true">→</span>
        </button>
        {file && (
          <button className="quiet" onClick={onReset}>
            Limpiar imagen
          </button>
        )}
      </div>
    </div>
  );
}
