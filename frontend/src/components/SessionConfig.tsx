type Props = {
  baseUrl: string;
  apiKey: string;
  onBaseUrl: (v: string) => void;
  onApiKey: (v: string) => void;
  onReset: () => void;
};
export function SessionConfig({
  baseUrl,
  apiKey,
  onBaseUrl,
  onApiKey,
  onReset,
}: Props) {
  return (
    <details className="session-config">
      <summary>Configurar sesión</summary>
      <div className="session-fields">
        <label>
          URL del servicio
          <input
            aria-label="URL backend"
            value={baseUrl}
            onChange={(e) => onBaseUrl(e.target.value)}
            spellCheck={false}
          />
        </label>
        <label>
          Credencial de acceso
          <input
            aria-label="API key"
            type="password"
            autoComplete="off"
            value={apiKey}
            onChange={(e) => onApiKey(e.target.value)}
          />
        </label>
        <button className="secondary" onClick={onReset}>
          Reiniciar demostración
        </button>
        <p>
          La credencial y la evidencia permanecen únicamente en esta sesión.
          Reiniciar limpia los datos locales de todos los paneles.
        </p>
      </div>
    </details>
  );
}
