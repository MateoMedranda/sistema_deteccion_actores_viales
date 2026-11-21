# Contrato de interacción del frontend —008

[Spec](../spec.md), [modelo de estados](../data-model.md) y [gateway](gateway.md). Parámetros cerrados para implementar y probar, no código entregado.

## Shell y sesión

WorkspaceTabs: tablist con Imagen/Video, tab/tabpanel vinculados, aria-selected y roving tabindex; flechas/Home/End recorren tabs, Enter/Espacio activa. Foco visible y targets>=44px. Los workspaces permanecen montados bajo epoch estable y el inactivo usa hidden; navegar no cambia generación ni keys, no crea/cancela trabajos. Si un panel ocupa foco cuando se oculta, vuelve al tab activo. Pausar reproductor al ocultar Video sin perder currentTime.

useManagedSession inicia POST /web/session. App deja de pedir URL/key; ConnectionStatus separa configuración, conexión autorizada y capacidades de análisis. No usar import.meta.env para secretos ni guardarlos en persistencia. ApiClient administrado conserva parser/AbortSignal/deadlines/TTL, añade cookie+CSRF y no X-API-Key. Firma/flujo directo anterior sigue disponible para callers/tests existentes.

Reset: invalidar generación, abortar descargas/sondeo, retirar src/Blob/URLs y datos de ambos espacios; cancelación best-effort de trabajos conocidos con timeout5s mientras la sesión es válida, luego DELETE sesión. Nunca reenganchar respuesta de otro epoch. Un refresh completo no reinicia automáticamente trabajos.

## Imagen y SceneViewport

Original canónico de007 como única escena; no fallback a upload/anotada. Toolbar: Ajustar,100%,200%,400%, Acercar/Alejar y Restablecer, escala legible. Intrínseca100%=1px original/px CSS; máximo4; ajuste<=1. Flechas de viewport40px, Shift120px; Home restablece encuadre cuando viewport tiene foco. No interceptar teclas dentro de botones/lista ni Ctrl/zoom global del navegador.

Escenario único W*s×H*s en viewport con overflow propio, max-height=min(70vh,720px) y min-width:0. Imagen y contornos porcentuales comparten caja de referencia. Conservar ancla bajo cursor/centro al escalar, clamp scroll a límites y no alterar posición de ficha/selección. ResizeObserver ignora dimensiones0 del panel oculto y conserva centro normalizado al mostrarlo.

Gestos: pointerdown recuerda origen; al desplazarse>=6px CSS se activa arrastre y captura de puntero. Movimiento ajusta scroll; pointerup libera captura y suprime solo el clic derivado de ese gesto. pointercancel/cambio de fuente limpian el gesto; clic/Enter/Espacio conservan selección previa007. Touch-action permite scroll de página en Ajustar cuando no hay pan; al ampliar se reserva solo el viewport para pan. Pellizco no es necesario; las acciones equivalentes son accesibles.

Foco>puntero>selección y colores007 siguen intactos; no cambiar hitboxes ni poner texto sobre imagen. Cerrar ficha no roba foco, lista equivalente44px. Scroll/zoom no altera crops, no ejecuta GET de preview adicional ni POST, y no renueva TTL.

## Video y autoencadenado

useVideoAnalysis/reductor tipado sustituye la coordinación manual de VideoJobPanel/EnrichmentPanel; esos callers anteriores pueden conservarse para compatibilidad, no duplicarse en la pantalla.

Cada análisis tiene identidad completa y una intención por tentativa:
1. Elegir archivo invalida fuente/selección/línea/count/enriquecimiento anteriores.
2. Analizar envía un upload con intención UUID, protegida sincrónicamente antes de await.
3. Recibo202 -> GET inmediato; no interpretar status queued del recibo repetido como estado actual.
4. Mientras queued/frames/encoding/publishing se sondea sin solapar cada1.2s, timeout10s. Encoding/publishing es indeterminado y no100% de etapa.
5. Video ready permite reproducir inmediatamente. Si eligible_track_count>0 iniciar una tentativa de enriquecimiento; si0, no aplicable. La transición tiene guarda por videoId/epoch/generation e idempotencia backend.
6. Pérdida de red ->interrupted; Reanudar hace GET. Recibo incierto de POST se recupera con la MISMA intención y payload aún vigentes, por acción explícita. Error conocido de negocio no se disfraza de interrupción.
7. Reintentar enriquecimiento tras fallo/cancelación conocido crea otra intención, sin repetir video. No hay bucle automático de intentos. Un400 no_eligible_vehicles es no aplicable;503/fallo conserva el medio.

Progreso presenta dos regiones con etiquetas y estados independientes. Conteos de cuadros pueden indicar total estimado; no comparar100% de cuadros con finalización del archivo. Conteos de enriquecimiento son unidades reales/track; completar con errores se etiqueta parcial, sin fingir lectura exitosa.

## Medio y conteo

VideoPlayer usa src relativa al gateway nativo autenticado, Range y metadata confirmada; no crea otro MP4 Blob completo. TTL conocido y epoch retiran src al vencer incluso pausado. Un error de medio consulta estado seguro para aplicar401/404/410; no crea otro job.

LineEditor/CountJobPanel permanecen dentro de VideoWorkspace, ligados a videoJobId. La línea de análisis usa la presentación procesada y su geometría, no un preview con orientación distinta. Cambiar fuente invalida línea/count. El artefacto contado mantiene contrato003 y no reemplaza silenciosamente al video de análisis.

Leyenda usa clases presentes y catálogo compartido; no inferir elegibilidad desde nombre/color ni llamar “vehículos” a summary.detections. No implementar clicks de contornos de video ni seguimiento visual de una ficha en esta etapa.

## Lista y ficha

Página25, solo página actual y ficha seleccionada. Siguiente/anterior accesibles; total y número de página explícitos. Navegación de página no crea análisis. Toda respuesta tardía verifica epoch/generation/videoJobId/enrichmentJobId; ficha además trackId.

Conservar y validar referencias de evidencia entregadas, sin truncar silenciosamente resultados. Mostrar atributos/placa/estados y confidencias observadas; ausencia histórica=origen desconocido. Con metadata confirmada, tiempo=i/fps se etiqueta “video procesado”; sin ella, solo cuadro/ref desconocida. No sugerir lectura del instante de reproducción ni solicitar crops exclusivos de imagen.

## Errores y retirada

401 de sesión/credencial =>retiro de ambos workspaces y ConnectionStatus de rechazo.403 de guardas del gateway =>sesión/operación inválida, limpiar contexto de sesión.404/410 de una fuente retira su grupo, no evidencia válida independiente.409/422/429/503/504 de tratamiento conservan original/video válidos con recuperación explícita. Deadline total y mínimo TTL se mantienen activos durante cuerpo/decode/stream.

## Casos mínimos de navegador

Tres tamaños y texto200%; alternar durante trabajos/TTL; canario y acceso protegido; zoom/drag/foco/cajas pequeñas; video limpio/codificación lenta; aceptación perdida/StrictMode/replay; cero elegibles; enriquecimiento parcial sin perder medio; múltiples páginas/evidencia temporal; reset/cancel/late; Range/búsqueda/pausa sin inferencias; conteo003. Estados/propuesta se revisan con capturas sintéticas, sin certificar WCAG completa por un test.
