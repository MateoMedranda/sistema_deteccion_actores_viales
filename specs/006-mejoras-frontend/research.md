# Research — Iteración 006

**Fecha**: 2026-11-20. Investigación de código y fuentes primarias; no incluye ejecución de pruebas de producto.

## 1. Mantener stack y separar recorrido de imágenes

**Decision**: React 18/TypeScript/Vite y CSS existentes; feature module, reducer y hooks locales; FastAPI/Python existente para soporte. Sin nuevos paquetes de producción ni actualización de versiones.
**Rationale**: La aplicación ya dispone de servicios y pruebas declaradas, pero `apiTypes.ts` no refleja la caja anidada del DTO y los paneles usan `any`/JSON. Corregir el contrato y el estado aporta más que añadir infraestructura.
**Alternatives considered**: Otro framework, store global o biblioteca visual completa aumentarían migración y riesgo sobre video.
**Evidence**: `frontend/package.json`, `frontend/src/services/apiTypes.ts`, `frontend/src/components/ImageAnalysisPanel.tsx`, `frontend/src/App.tsx`.

## 2. Botones sobre imagen y ficha en flujo

**Decision**: Contenedor que coincide con el área visible de la imagen, botones HTML con geometría porcentual y una lista equivalente. Una selección compartida y ficha lateral/en columna, sin modal obligatorio.
**Rationale**: Los botones nativos permiten foco y activación por teclado. La lista resuelve solapamientos y áreas diminutas sin ampliar cajas sobre vecinos. La posición se calcula sobre la imagen real; si se usa contain dentro de una caja fija, se descuentan márgenes.
**Alternatives considered**: Canvas interactivo exige reconstruir semántica e hit testing; modal obligatorio añade manejo de foco innecesario.
**Sources**: [WAI Button Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/), [MDN object-fit](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/object-fit).

## 3. Orquestación y respuestas tardías

**Decision**: El clic inicia detección y encadena enriquecimiento. Guard sincrónico y generación por fuente/sesión; AbortSignal, temporizadores y registro de recursos. Polling secuencial cada 1200 ms, sin reinicios automáticos ambiguos de POST.
**Rationale**: AbortController cancela la espera del cliente, no garantiza cancelación del trabajo remoto. Los efectos necesitan limpieza; StrictMode ya está activo. Reset actual limpia variables de App pero deja estados internos montados.
**Alternatives considered**: POST en efecto de montaje y confiar solo en abort no evitan duplicados ni resultados obsoletos. Idempotencia persistida en servidor se difiere: no es necesaria para impedir doble clic, y no se afirma garantizar exactamente una ejecución ante una pérdida de respuesta.
**Sources**: [React useEffect](https://react.dev/reference/react/useEffect), [MDN AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController), [MDN revokeObjectURL](https://developer.mozilla.org/en-US/docs/Web/API/URL/revokeObjectURL_static).

## 4. Imagen canónica y evidencia

**Decision**: Normalización EXIF/RGB una vez, imagen PNG canónica sin metadatos sensibles, dimensiones únicas y geometría clamp compartida antes de asignar IDs. Exponer ese mismo original por ruta autenticada temporal. Crop vehicular local, placa relativa a ese crop.
**Rationale**: PIL obtiene dimensiones del upload mientras OpenCV decodifica detección/enriquecimiento; no hay normalización explícita común. Es riesgo observado, no un fallo ya reproducido. `_to_response()` fuerza mínimo de un píxel mientras `crop_vehicle()` rechaza degeneradas. La ruta original evita que navegador y servidor recorten versiones orientadas de manera distinta.
**Alternatives considered**: Confiar en el archivo local puede funcionar pero necesita probar la equivalencia de orientación; crear un endpoint por crop duplica manejo de artefactos. Se reutiliza el original que ya retiene el servidor.
**Sources**: [Pillow ImageOps.exif_transpose](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html), [FastAPI Responses](https://fastapi.tiangolo.com/advanced/custom-response/), [MDN drawImage](https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/drawImage).
**Compatibility**: Verificar la API con Pillow >=10,<12 instalada; no usar opciones añadidas recientemente. Medir la normalización contra imágenes aprobadas; no cambiar preprocesamiento de modelo sin evidencia.

## 5. Corregir disponibilidad y privacidad existentes

**Decision**: Readiness a partir de adaptadores, estados por rama, JSON/table output saneados y transiciones terminales atómicas. Janitor cada 1 s, margen de purga <=2 s y cierre ordenado.
**Rationale**: `lifespan.py` puede marcar ready con adaptadores None. `enrichment_job_store.finish()` persiste JSON crudo aunque la tabla de placas redacta estados no read. Cancel y finish no comparten transacción completa; worker no comprueba estado entre unidades. La limpieza de originales depende actualmente de create/get.
**Alternatives considered**: Resolverlo solo en UI no corrige lo servido/persistido ni detiene publicación tardía. Cambiar modelos no resuelve estos defectos de ciclo de vida.
**Evidence**: `app/core/lifespan.py`, `app/services/enrichment_job_store.py`, `app/services/enrichment_worker.py`, `app/services/image_detection_store.py`, `tests/unit/test_enrichment_job_store.py`.

## 6. Identidad y alcance de resultados

**Decision**: `request_id` identifica fuente; `detection_id` identifica una detección dentro de ella; `track_id` sigue null en imagen. Publicar enriquecimiento al completed, no incremental. Durante processing se muestran datos básicos y pendientes; parcial denota ramas fallidas con datos válidos conservados.
**Rationale**: El worker actual publica al final. Esto satisface la especificación sin prometer parciales que no existen. La imagen estática no prueba seguimiento temporal, y añadir un contador no lo convertiría en tracking.
**Alternatives considered**: Publicación por unidad exigiría protocolo de snapshot/paginación/concurrencia adicional; se difiere. Seguimiento real para imágenes requeriría fuentes temporales nuevas, fuera de alcance.
**Evidence**: `app/services/enrichment_job_service.py`, `app/services/enrichment_worker.py`, `specs/004-extraccion-caracteristicas-y-placas/data-model.md`.

## 7. Verificación visual y accesibilidad

**Decision**: Paleta sobria sin gradientes, tokens CSS y scope del módulo para preservar LineEditor. Capturas de estados en 360/768/1440, texto 200%, teclado/toque y evaluación con personas según SC-007.
**Rationale**: Los snapshots necesitan el mismo entorno y revisión humana de la primera referencia. Las resoluciones de la especificación no equivalen por sí solas a certificar conformidad WCAG completa.
**Alternatives considered**: Afirmar accesibilidad solo por tests DOM o aprobar automáticamente capturas iniciales no verifica legibilidad.
**Sources**: [W3C Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html), [Playwright visual comparisons](https://playwright.dev/docs/test-snapshots).

## Resultado

Decisiones técnicas resueltas para planificar. Recursos externos restantes: pesos/manifiestos válidos, medios controlados y acceso al entorno de evaluación. No se ejecutaron inferencias ni mediciones. Los cambios de backend identificados forman parte del trabajo de 006, según ampliación expresa del usuario.

## Ajustes tras análisis autorizado — 2026-11-20

**Decision**: Concretar plazos de imágenes (120/15/10/30 s por tipo de solicitud y 120 s por ciclo de observación, siempre acotados por TTL), instrumentación correlacionada de duración/RSS y fixtures explícitos de capacidades. Mantener las 69 tareas e integrar correcciones en sus responsabilidades existentes. T033 es MVP parcial de orquestación; aceptación de selección de US1 después de T039/T040.
**Rationale**: Resuelve C1/I1/A1/I2 del análisis sin atribuir observabilidad al simple hecho de ejecutar suites ni readiness a una bandera falsa. El contrato OpenAPI pasa a enlazar las respuestas con POST imagen, GET original y GET readiness mediante referencias locales resolubles.
**Alternatives considered**: Reintentos automáticos de POST, plazos ilimitados, flags ready forzados, cierre anticipado de US1 y esquemas sin operaciones vinculadas no satisfacen los criterios acordados.
