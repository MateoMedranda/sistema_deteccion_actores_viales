import {classPresentation} from "../image-analysis/classPresentation";
import { useEffect, useState } from "react";
import { ApiClient, ClientError } from "../../services/apiClient";
import type { Track } from "./progressiveTypes";
import { clock } from "./VideoTimeline";
function Crop({
  client,
  path,
  label,
  expiry,
  onUnavailable,
}: {
  client: ApiClient;
  path: string;
  label: string;
  expiry: string;
  onUnavailable: () => void;
}) {
  const [url, setUrl] = useState<string>();
  useEffect(() => {
    const c = new AbortController();
    let object: string | undefined;
    void client
      .blob(path, { signal: c.signal, expiresAt: expiry, timeoutMs: 10000 })
      .then((b) => {
        if (!c.signal.aborted) {
          object = URL.createObjectURL(b);
          setUrl(object);
        }
      })
      .catch((e) => {
        if (
          !c.signal.aborted &&
          e instanceof ClientError &&
          [401, 403, 410].includes(e.status)
        )
          onUnavailable();
      });
    return () => {
      c.abort();
      if (object) URL.revokeObjectURL(object);
      setUrl(undefined);
    };
  }, [client, path, expiry]);
  return url ? (
    <img src={url} alt={label} />
  ) : (
    <p>Preparando {label.toLowerCase()}…</p>
  );
}
export function ProgressiveTrackResults({
  client,
  tracks,
  selected,
  onSelect,
  onUnavailable,
}: {
  client: ApiClient;
  tracks: Track[];
  selected?: number;
  onSelect: (id: number) => void;
  onUnavailable: () => void;
}) {
  const track = tracks.find((t) => t.track_id === selected);
  return (
    <aside
      className="progressive-details"
      aria-label="Vehículos y enriquecimiento"
    >
      <h3>
        Vehículos detectados <span>{tracks.length}</span>
      </h3>
      <p className="muted">
        Pausa y selecciona una caja o un vehículo de la lista.
      </p>
      <div className="progressive-track-list">
        {tracks.map((t) => (
          <button
            key={t.unit_id}
            aria-pressed={selected === t.track_id}
            onClick={() => onSelect(t.track_id)}
          >
            #{t.track_id} · {classPresentation(t.class_name).label}
            <small>
              {t.final
                ? "Resultado final"
                : t.evidence.length
                  ? "Resultado provisional"
                  : "Preparando datos"}
            </small>
          </button>
        ))}
      </div>
      {track ? (
        <section aria-labelledby="progressive-track-heading">
          <h3 id="progressive-track-heading">Vehículo #{track.track_id}</h3>
          <p>
            {track.final
              ? "Datos finales"
              : "Datos provisionales · pueden actualizarse"}
          </p>
          <dl>
            <dt>Clase</dt>
            <dd>{classPresentation(track.class_name).label}</dd>
            <dt>Placa</dt>
            <dd>
              {track.plate.text ??
                (track.plate.status === "pending"
                  ? "En consulta…"
                  : track.plate.status === "not_detected"
                    ? "No detectada"
                    : "No disponible")}
            </dd>
            {track.attributes.items.map((a) => (
              <div key={a.name}>
                <dt>{a.name}</dt>
                <dd>
                  {a.value} · {Math.round(a.confidence * 100)}%
                </dd>
              </div>
            ))}
          </dl>
          {track.evidence.slice(0, 1).map((e) => (
            <div key={e.evidence_id} className="progressive-crops">
              <small>
                Imagen representativa del instante {clock(e.time_us)} · no
                cambia la reproducción
              </small>
              {e.vehicle_url && (
                <Crop
                  client={client}
                  path={e.vehicle_url}
                  label="Recorte del vehículo"
                  expiry={e.expires_at}
                  onUnavailable={onUnavailable}
                />
              )}
              {e.plate_url && (
                <Crop
                  client={client}
                  path={e.plate_url}
                  label="Recorte original de la placa"
                  expiry={e.expires_at}
                  onUnavailable={onUnavailable}
                />
              )}
            </div>
          ))}
        </section>
      ) : (
        <p>Selecciona un vehículo para consultar sus datos.</p>
      )}
    </aside>
  );
}
