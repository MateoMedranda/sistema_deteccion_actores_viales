# Implementation Plan: Exploración de imágenes y video

**Branch**: feature/008-exploracion-imagen-video | **Date**: 2026-11-21 | **Spec**: [spec.md](spec.md)

**Input**: specs/008-exploracion-imagen-video/spec.md. Checkout principal; preservar contenido e índice existentes. Cada etapa completada se confirma con su commit.

## Summary

Dar la misma visibilidad a Imagen y Video, configurar el acceso por entorno protegido, ampliar la escena original y ofrecer video limpio/estable con enriquecimiento automático y progreso honesto. Mantener modelos, seguimiento raw, conteo, política OCR y contratos anteriores.

Arquitectura: backend detector FastAPI existente; gateway web FastAPI ligero y separado de modelos, con configuración WEB_* privada y sesión same-origin; frontend React conservado, dos workspaces montados, zoom local, MP4 anotado por servidor y consulta de tracks por lista/ficha. La selección directa sobre video pausado sigue como propuesta posterior. [Research](research.md) fija12 decisiones; [contratos](contracts/backend-additions.md) delimitan las adiciones compatibles.

## Technical Context

**Language/Version**: Python3.12 (instalado3.12.15), TypeScript/React18 existentes.
**Primary Dependencies**: FastAPI0.115.14, Pydantic2.14.1, Uvicorn0.54.0 y OpenCV4.14.0.94 instalados; Vite5/Vitest2/Playwright existentes. HTTPX0.28.1 pasa al runtime dentro del rango actual >=0.27,<1. No actualizar modelos/librerías por esta fase.
**Storage**: SQLite y archivos temporales existentes; columnas aditivas de fase/framecount/idempotencia. Sesiones del gateway en RAM acotada. Sin historial ni nuevos medios de evidencia.
**Testing**: pytest, Vitest/build y Playwright; fixtures controlados y protocolo de fluidez/rendimiento, privacidad de canarios y contratos JSON Schema.
**Target Platform**: Desarrollo/validación Windows; navegador Chromium en360/768/1440. Despliegue local loopback o ingreso privado/autenticado existente, HTTPS cuando sea remoto.
**Project Type**: Aplicación web más API de análisis; gateway de entrega sin inferencia.
**Performance Goals**: zoom p95<=200ms, UI activa<=1s; jitter>=20% de reducción en tramos no estables; IoU>=.90 en>=95% de cuadros válidos; desfase<=1cuadro;3 pares de medidas con mediana temporal y pico RSS<=110% baseline.
**Constraints**: API key nunca en navegador; identidad/TTL mínimos; no modelos, pesos, umbrales o autenticación de backend nuevos. Cajas de presentación no cambian observaciones usadas por conteo/enriquecimiento.
**Scale/Scope**: Una imagen y un video vigentes por sesión. Límites de backend conservados (predeterminados: video100MiB/120s/1920×1080/30FPS/3600cuadros,1 worker y cola20). Gateway16 solicitudes/2uploads, sesiones128/900s; no colas nuevas ilimitadas.

## Constitution Check

GATE antes de Phase0 y revalidado después del diseño:

| Principio | Inicial | Diseño |
|---|---|---|
| I Modularidad | PASS | API fina, gateway app/web sin importar app.main/model lifespan, helpers de presentación puros y transportes tipados. |
| II Validación/trazabilidad | PASS | allowlist, límites/deadlines, esquema aditivo, logs seguros y métricas de publicación efectiva. |
| III Seguridad/datos | PASS condicionado al despliegue autorizado | Clave server-only; un principal por instancia; cookie/CSRF no sustituyen ingreso privado. Dueño/TTL antes de cada evidencia, no historial ni nueva retención. |
| IV Pruebas/modelo | PASS | Modelos/thresholds/política intactos; fixtures y baseline congelados; pruebas de imagen/video/count/access y gates no afirmados antes de medir. |
| V Recursos | PASS | No segunda carga de modelos, HTTPX/streams acotados, filtro causal de estado actual, worker/proceso retenidos hasta terminar y medición reproducible. |

Sin excepción constitucional. Un despliegue público sin ingreso autorizado NO satisface este diseño y queda bloqueado; no se lo habilita como fallback. Los resultados de rendimiento/fluidez son pendientes de implementación, no PASS de producto.

## Project Structure

### Documentation (this feature)

~~~text
specs/008-exploracion-imagen-video/
  spec.md
  checklists/requirements.md
  propuesta-inspeccion-video.md
  plan.md
  research.md
  data-model.md
  validation-protocol.md
  contracts/gateway.md
  contracts/backend-additions.md
  contracts/frontend-interactions.md
  contracts/schemas.json
  quickstart.md
  tasks.md                       # futuro speckit-tasks; no se crea aquí
~~~

### Source Code (repository root, destinos futuros)

~~~text
app/web/{main,settings,sessions,proxy}.py       # gateway sin modelos
app/api/routes/web_policy.py                  # política protegida y no sensible
app/services/web_policy_service.py
app/domain/class_presentation.json            # tabla007 preservada
app/services/class_presentation.py
app/services/video_presentation.py            # gated-ema-v1 y dibujo sin rótulos
app/services/video_processing.py
app/services/video_job_store.py
app/services/video_job_service.py
app/services/video_worker.py
app/services/enrichment_job_store.py
app/services/enrichment_job_service.py
app/domain/{models,schemas}.py
app/api/routes/{video_jobs,enrichment_jobs}.py
app/main.py                                   # incluir política; no alterar auth
app/core/lifespan.py                          # conectar limpieza segura de artefactos
frontend/src/App.tsx
frontend/src/components/{WorkspaceTabs,ConnectionStatus}.tsx
frontend/src/hooks/useManagedSession.ts
frontend/src/services/{apiClient,apiTypes}.ts
frontend/src/features/image-analysis/{SceneViewport,AnnotatedImageViewer,ImageWorkspace}.tsx
frontend/src/features/image-analysis/{classPresentation.ts,image-analysis.css}
frontend/src/features/video-analysis/
  VideoWorkspace.tsx
  videoAnalysisReducer.ts
  useVideoAnalysis.ts
  VideoProgress.tsx
  VideoPlayer.tsx
  VideoTrackList.tsx
  VideoTrackDetails.tsx
frontend/src/components/{LineEditor,CountJobPanel}.tsx  # composición, identidad conservada
frontend/vite.config.ts                       # proxy local sin secretos VITE_*
.env.web.example / .gitignore / pyproject.toml
tests/{unit,integration,contract,e2e,performance}/
tests/e2e/build_video_presentation_fixtures.py
scripts/evaluate_video_presentation.py
frontend/tests/ y frontend/e2e/
~~~

**Structure Decision**: Mantener app/ y frontend/, sin crear otro motor/backend de inferencia. app/web es un proceso de entrega/relay del mismo paquete, con lifecycle propio. Los archivos de fuente anteriores NO se crean en esta etapa.

## Phase 0 — Research

Completada en [research.md](research.md): inspección del código actual y tres investigaciones de solo lectura. Se resolvieron seguridad de entorno, transporte, estado/zoom, paleta, filtro, finalización, correspondencia temporal e idempotencia. No quedan aclaraciones técnicas abiertas.

Hallazgos de integración que el plan debe resolver:
- App exige URL/key manual; ApiClient siempre transmite X-API-Key.
- Ocultar desmontando useLegacyJob cancela trabajos.
- Video quema rótulos verdes; el100% de cuadros antecede a codificar.
- finish fuerza total estimado y necesita coordinación TTL/cancelación.
- POST de enriquecimiento no es idempotente; la vista muestra JSON y página1.
- El parser pierde referencias de evidencia; summary cuenta observaciones, no vehículos.

## Phase 1 — Design

### A. Gateway y política protegida

Entrada app.web.main:app sin lifespan del detector. Configuración en .env.web/WEB_*, fuera de Vite. Backend mantiene X-API-Key/Principal; un endpoint protegido GET /api/v1/web-policy devuelve límites/capacidades, sin secretos. Bootstrap lo consulta para acreditar configuración y autorización sin crear trabajos.

Frontend gestionado usa /web-api, cookie de sesión/CSRF y bootstrap; modo de clave directa de ApiClient se conserva para clientes/tests previos. El relay solo acepta operaciones de [gateway.md](contracts/gateway.md), sin URLs ni credenciales del solicitante. Estático de producción sirve frontend/dist; desarrollo Vite4173 retransmite a gateway4174 manteniendo Host/Origin. Backend8000 queda separado.

Native video usa cookies y relay de contenido de paths exactos con Range/CORP/TTL; no se descarga entero en un Blob. Session reset cancela consumos conocidos, invalida epoch, limpia ambos workspaces y revoca la cookie; la configuración del operador permanece.

### B. Estado de interfaz y zoom

Dos paneles montados con hidden, sin keys que dependan del modo. Estado global únicamente sesión/activeMode; cada workspace conserva su generación, fuente y resultados vigentes. TTL continúa oculto; Video se pausa al ocultar sin cancelar trabajos.

SceneViewport mantiene dimensiones naturales*escala y scroll local. Botones Ajustar/100/200/400%, ancla estable y arrastre>=6px que no activa selección. Proyección porcentual y recortes canónicos de007 intactos; eventos/foco/selección externos siguen independientes. [Contrato UI](contracts/frontend-interactions.md).

### C. Presentación del video y finalización

Tabla única de clases mantiene exactamente007, sin inferir elegibilidad. Leyenda de todas las clases con aviso general de elegibilidad del servidor y etiqueta de clase desconocida; no requiere una matriz de elegibilidad por clase ni campos API adicionales. Helper puro filtra solo cajas actuales por track/class; dibuja contornos con color y trazos auxiliares, sin putText. Raw FrameDetection se almacena íntegra y sigue alimentando conteo/evidencia. La temporalidad del MP4 se conserva en CFR; no se incorpora una capa interactiva temporal al reproductor.

Fase explícita encoding/publishing con progreso indeterminado. Corregir total al EOF real, conservar contador real y confirmar metadatos de salida solo para nuevas ejecuciones. Históricos conservan null en fase/metadata/conteo elegible/clases, con frame_total_confirmed=false no nullable; ausencia de API anterior se normaliza a false y null explícito se rechaza. Cancelar/vencer durante FFmpeg detiene el proceso antes de liberar worker; parciales se eliminan y finish publica atómicamente solo mientras processing/vigente. Métricas usan ese desenlace, no solo éxito de transformación.

### D. Idempotencia y enriquecimiento

Header opcional y columnas en filas actuales, sin nueva cola. Validar/hashear upload bajo cotas; admisión/replay atómicos por propietario, clave y fingerprint. Replays responden el recibo original y se consulta GET para estado vigente. Legacy sin header mantiene su comportamiento.

useVideoAnalysis protege la intención antes de await y crea enriquecimiento una sola vez tras video completado con eligible_track_count>0. Un resultado incierto reutiliza la misma intención; fallo conocido solo se reintenta por acción explícita y nueva tentativa. Cero elegibles=no aplicable. Video disponible aunque enriquecimiento continúe/falle.

Lista25/página, ficha por identidad completa y evidencia representativa por cuadro/tiempo del MP4 procesado; sin crops de video nuevos ni falsa lectura en cada instante. Conteo usa fuente procesada/identidad correctas y mantiene contrato003.

## Orden de implementación y paquetes

1. **P0** Congelar baseline, fixtures, contratos e identidades antes de cambiar comportamiento.
2. **B1/F1** Política protegida, gateway, transporte de sesión y prueba de canario; preservar acceso directo previo.
3. **F2** Tabs y SceneViewport; independientes de suavizado de video una vez estable la sesión.
4. **B2** Paleta compartida, gated-ema-v1, fases/EOF/cancelación/publicación y sus carreras.
5. **B3** Idempotencia video/enriquecimiento y metadatos aditivos; probar concurrencia/replay/TTL.
6. **F3** VideoWorkspace, autoencadenado, progreso/medio/resultados/errores y conteo.
7. **V1** Suites y mediciones [validation-protocol.md](validation-protocol.md), revisión visual y propuesta de pausa revisada.
8. **D1** Auditoría final, documentación de despliegue y commit de etapa. No cerrar aceptación si falla un gate.

No crear tasks.md en plan; la generación siguiente convertirá estos paquetes en tareas con dependencias y pruebas primero.

## Trazabilidad de entrega

| Área | Requisitos | Acreditación |
|---|---|---|
| Modos/estado | FR-001–003/024 | SC-001/007/009, cambio durante trabajo/TTL |
| Configuración segura | FR-004–007 | SC-002, canario/ingreso/cookie/relay/compatibilidad |
| Zoom | FR-008–011 | SC-003,10 escenas/3densas/1px/p95 |
| Video/presentación | FR-012–015/027 | SC-004–006,6clips/3tramos/gates |
| Autoenriquecimiento | FR-016–020 | SC-007/008, intención/recuperación/estado |
| Fichas/conteo | FR-021–024 | SC-008/009, páginas/tiempo/count |
| Propuesta y conservación | FR-025–028 | SC-009/010, sin selección pausada implementada ni aceptación OCR ficticia |

## Validation strategy

Contratos nuevos se validan con JSON Schema y ejemplos; implement agregará pruebas de API/modelos, gateway con upstream inyectado, secretos/streams/CSRF, reducers/componentes, geometría y Playwright con imagen/video. Medición visual, latencia, memoria y jitter se ejecutará después de implementar con condiciones congeladas, sin atribuir exactitud real a fixtures. [Quickstart](quickstart.md) separa comandos ya existentes de los previstos.

## Complexity Tracking

Sin violaciones ni excepciones solicitadas. El gateway separado evita cargar modelos dos veces y permite proteger la clave sin cambiar la autenticación de la API; exige dos procesos Python, no otra base de datos/cola. Se aceptan únicamente migraciones aditivas de las filas temporales actuales. La selección interactiva pausada, nuevos medios, identidades persistentes y rediseño VFR quedan fuera.

## Aclaraciones aprobadas tras analyze

I1: X-UI-Intent es obligatorio en el gateway para upload/enriquecimiento de video (ausencia422 web_intent_required, UUID inválido422 web_intent_invalid); opcional en imagen. Idempotency-Key de API directa conserva compatibilidad opcional.

I2: frame_total_confirmed es booleano no nullable, false para históricos/no confirmado, NOT NULL DEFAULT 0; ausencia legacy se normaliza a false y null explícito se rechaza. Los demás cuatro campos aditivos conservan sus null autorizados.

U1: la leyenda muestra todas las clases y el aviso general definido en el contrato UI; clase desconocida tiene indicador propio. No se atribuye elegibilidad individual ni se añaden campos API/configuración al frontend. Casos mixtos, null/vacío y total elegible0 quedan en T039/T041.

Se conservan82 tareas/439PTS; T029/T032/T039/T040/T041/T047/T051/T075 incorporan las aclaraciones. Contratos revisados:16 definiciones,13 ejemplos válidos y9 inválidos comprobados con jsonschema4.23.0 en entorno aislado. Las cifras11/7 siguientes corresponden a la verificación original de plan; las actuales son13/9. No se ejecutó código de producto.

## Verificación de esta etapa

Diseño revisado contra los5 principios constitucionales y los28 requisitos/10 criterios de008. Contratos:16 definiciones JSON Schema2020-12,11 ejemplos válidos y7 ejemplos inválidos rechazados; referencias locales resueltas y enlaces Markdown comprobados. Validación con jsonschema4.23.0 en entorno temporal aislado mediante uv --isolated --no-project, sin modificar dependencias del proyecto.

No se ejecutaron inferencias, benchmarks ni pruebas de producto; app/web, migraciones y funciones descritas son trabajo futuro. Ninguna medición de fluidez/rendimiento se declara lograda. La especificación, checklist y propuesta previos se conservan sin reescritura. Esta etapa termina con los10 documentos de planificación y su commit; después corresponde speckit-tasks.
