import { ClientError } from "../../services/apiClient";
export function analysisMessage(error: unknown): string {
  if (error instanceof ClientError) {
    if (error.status === 413)
      return "El archivo supera el tamaño permitido por el servicio. Selecciona una imagen más pequeña.";
    if (error.status === 415 || error.status === 422)
      return "No se pudo validar la imagen. Usa un JPEG o PNG válido con una resolución admitida.";
    if (error.status === 401)
      return "La credencial no es válida. Revisa la configuración de sesión.";
    if (error.status === 404 || error.status === 410)
      return "La evidencia ya no está disponible. Selecciona la imagen y analiza de nuevo.";
    if (error.status === 503)
      return "El servicio no puede completar esta etapa. Revisa su disponibilidad y vuelve a intentarlo.";
    if (error.detail.code === "request_timeout")
      return "Se alcanzó el tiempo de espera. Revisa el estado antes de volver a intentarlo.";
    if (error.detail.code === "invalid_response")
      return "La respuesta no es válida. No se mostrarán datos sin una asociación fiable.";
  }
  return "No fue posible completar la consulta. Revisa la conexión y vuelve a intentarlo.";
}
