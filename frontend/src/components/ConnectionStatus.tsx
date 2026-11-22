const labels:Record<string,string>={
 connecting:"Conectando con el servicio…",ready:"Servicio conectado",configuration_missing:"El servicio está pendiente de configuración.",configuration_invalid:"La configuración del servicio necesita revisión.",upstream_unavailable:"El servicio no está disponible. Puedes reintentar.",access_rejected:"Acceso rechazado. Contacta al responsable del servicio.",expired:"La sesión ha vencido. Conecta de nuevo para comenzar."};
export function ConnectionStatus({state,onRetry,onReset}:{state:string;onRetry:()=>void;onReset:()=>void}){
 return <section className="connection-status" aria-label="Estado de conexión"><p role="status"><span className={"connection-dot "+state} aria-hidden="true"/>{labels[state]??labels.upstream_unavailable}</p>{state==="ready"?<button onClick={onReset}>Reiniciar sesión</button>:state!=="connecting"&&<button onClick={onRetry}>Reintentar conexión</button>}</section>;
}
