# Investigación técnica: Interfaz web prototipo vial

## Decisión: React 18 + Vite + TypeScript, sin gestor global adicional

**Rationale**: React con Vite permite un prototipo rápido y modular. TypeScript mantiene tipados los contratos FastAPI. Un DemoSessionProvider con hooks por dominio es suficiente para una sola fuente y un video activo; reduce dependencias y facilita que otro integrante cambie los paneles.

**Alternativas consideradas**: Redux/Zustand se descartan por el alcance de una sesión única; HTML servido por FastAPI se descarta porque acoplaría presentación y microservicio.

## Decisión: API key y URL base solo en memoria

**Rationale**: La API key viaja en X-API-Key, nunca en URL, localStorage, sessionStorage, logs ni mensajes. La URL base parte de http://127.0.0.1:8000, se valida como HTTP(S), se normaliza sin barra final y desaparece al reiniciar o cerrar la navegación.

**Alternativas consideradas**: Persistir la configuración mejora comodidad pero vulnera FR-001 y FR-010; una URL compilada impediría probar en otro equipo o puerto.

## Decisión: fetch autenticado y URL de objeto para artefactos protegidos

**Rationale**: Los recursos anotados exigen X-API-Key; elementos img y video no pueden adjuntar esa cabecera. El cliente los solicitará con fetch, comprobará el estado HTTP, creará un Blob y usará URL.createObjectURL. Todo URL de objeto se revoca al sustituirlo, reiniciar o desmontar el componente.

**Alternativas consideradas**: Usar directamente la URL devuelta como src fallaría la autenticación y podría exponer una URL de artefacto; hacer públicos los artefactos viola el aislamiento por propietario.

## Decisión: polling secuencial de 1–2 segundos

**Rationale**: El backend publica estados mediante GET, no SSE/WebSocket. setTimeout después de terminar cada petición evita consultas superpuestas; se detiene en completed, failed, cancelled, expired, 404/409/410, reinicio o desmontaje.

**Alternativas consideradas**: setInterval puede solapar solicitudes lentas; SSE/WebSocket requeriría contratos que el backend aún no expone.

## Decisión: SVG responsivo para la línea de conteo

**Rationale**: Un overlay SVG permite visualizar, arrastrar, ajustar y borrar los dos extremos. ResizeObserver reubica la representación a partir de puntos normalizados; la solicitud usa los valores originales en [0,1], sin depender de píxeles de la pantalla. Una línea de longitud cero se bloquea localmente.

**Alternativas consideradas**: Canvas es válido, pero SVG simplifica accesibilidad, pruebas y manipulación de dos puntos en este alcance.

## Decisión: CORS explícito y cancelación de conteo como compatibilidad del backend

**Rationale**: Vite opera en un origen distinto del backend. Se añadirá una configuración de orígenes permitidos, con valores locales de desarrollo explícitos y sin * cuando se permite X-API-Key. Además, el backend tiene DELETE para video y enriquecimiento, pero no para conteo; se añadirá DELETE /api/v1/count-jobs/{countJobId} con la misma semántica segura de propietario y cancelación.

**Alternativas consideradas**: Un proxy de Vite solo sirve desarrollo local y no cubre URL base editable o una compilación estática. Limpiar únicamente el estado del navegador dejaría conteos activos y contradice FR-010.

## Decisión: pruebas por capas sin modelos reales

**Rationale**: Vitest/React Testing Library validan lógica y componentes con fetch simulado; Playwright cubre recorridos contra una API simulada. Pytest verifica CORS y el nuevo DELETE. Así se obtienen pruebas repetibles sin pesos, GPU ni procesamiento largo.

**Alternativas consideradas**: Depender de inferencia real en todas las pruebas vuelve la demostración lenta, frágil y dependiente de modelos privados.

