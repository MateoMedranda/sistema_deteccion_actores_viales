# Validación de implementación008

Baseline congelada desde c4857a1 en baseline.json y tests/fixtures/video_presentation/legacy_renderer.py. El archivo generado tsconfig.tsbuildinfo previo se conserva por separado y queda fuera de commits.

## Registro

- Checklist requirements.md:16/16, solo lectura.
- Frontend previo:28 archivos/78 pruebas PASS.
- Backend previo:253 pruebas PASS (51.04s).
- Fixtures008:10 escenas (3densas) y6clips sintéticos,2densos con21actores;3segmentos de150cuadros. Manifiesto/raw/referencias congelados antes de evaluar la candidata.
- Los fixtures verifican presentación/lifecycle; no certifican precisión real de detector/OCR.

Pendientes externos conservados:006/T067–T068 y007/T061–T064/T070. Los gates de coste completo, fluidez, geometría y revisión visual se registrarán con sus medidas efectivas.

## US1
T001–T012 completadas. Vitest:2 pruebas nuevas PASS (tabs/TTL oculto), build PASS; Playwright:3 recorridos PASS en360/768/1440 y texto200%, sin nuevas operaciones por navegar. Transporte manual se conserva temporalmente hasta US2.

## US2
T013–T027 completadas. Gateway separado con sesiones RAM/CSRF/allowlist/cotas/Range y web-policy autenticada; cliente directo conservado.11 pruebas backend de gateway/política PASS;2 pruebas de transporte/reset frontend PASS y build PASS. Playwright009:9 recorridos de sesión/imagen/navegación PASS en3tamaños, sin X-API-Key en solicitudes del navegador. Los límites de streams/ingreso local/privado se conservan; despliegue público no habilitado.

## US4
T028–T044 completadas como incremento de presentación. Paleta007 compartida, filtro gated-ema-v1 solo visual, raw preservado, EOF real, metadata confirmada y fases encoding/publishing. Supervisor FFmpeg cancelable retiene worker hasta reap; janitor conserva rutas purgadas mientras estén en uso.11 pruebas seleccionadas de filtro/store/encoder/publicación/evaluador PASS,2 pruebas frontend nuevas PASS y build PASS. Video controlado real: navegador en3tamaños PASS. Evaluador sintético6clips: quality_pass=true con IoU/lag/jitter por segmento en video-presentation-summary.json. Esto no acredita precisión del detector/OCR ni SC-006 con modelos reales, que permanece pendiente en T077.

## US5
Idempotencia opcional directa (hash incremental y UNIQUE por propietario), intención administrada HMAC y generación monotónica; recuperación explícita usa la misma intención. Un rechazo terminal permite nueva tentativa sin repetir detección. Polling y TTL independientes, medio nativo y conteo procesado.
Backend completo:280 pruebas PASS (57.80s). Vitest focal:6 pruebas PASS; build PASS. Navegador:24 recorridos PASS (42.4s),8 casos en3 tamaños. Éxito/conteo usan gateway y upstream controlado reales; encoding/cero elegibles/503/recibo perdido/cancelado/TTL usan respuestas de navegador controladas. No equivalen a modelos reales. Etiqueta parcial por página se cierra con US6/T056.

## Reserva adicional de cruces
Antes de medir este caso se fija un séptimo clip opposing-crossing: dos trayectorias opuestas en la misma fila (x=8+2i y x=550-2i),150cuadros30FPS640×360, IDs/clases estables, más un control estacionario. El nombre dense-crossing del conjunto original no implica cruce geométrico: ese clip sigue siendo una escena densa de flujo, sin alterar sus raw/referencias ni las constantes del filtro. El nuevo caso se guarda como reserva adicional y se evalúa por separado antes de agregarlo al informe; no sustituye ni ajusta los seis casos ya observados.

## US3 y US6: implementación y primera verificación
SceneViewport comparte un escenario intrínseco con los contornos: fit/100/200/400%, pan local, ancla normalizada, teclado y supresión del clic derivado del arrastre. No repite análisis ni modifica recortes.
Lista/ficha de video usa track_id real, página25, consulta abortable por identidad, TTL incluso oculta y referencias de evidencia validadas. Se sustituye página/ficha sin historial. Las referencias CFR i/fps se distinguen de currentTime; procedencia desconocida no se deduce de used_enhancement. No se consultan crops de imagen para video.
Primera ejecución de zoom+fichas:6 recorridos PASS (23.4s),3 tamaños y texto200%; la medición final repetirá tras reforzar fixtures de éxito/selección y persistirá agregados de zoom en zoom-summary.json. Fichas recorren61 resultados en3 páginas y0POST/crops nuevos. Las tareas T065/T074 se cierran tras ese registro final. Propuesta de inspección pausada revisada en propuesta-inspeccion-video.md.

## Reserva adicional de cruces
Antes de medir este caso se fija un séptimo clip opposing-crossing: dos trayectorias opuestas en la misma fila (x=8+2i y x=550-2i),150cuadros30FPS640×360, IDs/clases estables, más un control estacionario. El nombre dense-crossing del conjunto original no implica cruce geométrico: ese clip sigue siendo una escena densa de flujo, sin alterar sus raw/referencias ni las constantes del filtro. El nuevo caso se guarda como reserva adicional y se evalúa por separado antes de agregarlo al informe; no sustituye ni ajusta los seis casos ya observados.

## Coste completo del procesador: primeros seis clips
Se ejecutaron18 pares/36 brazos completos con el detector/tracker real y los pesos configurados en CPU, un brazo a la vez. Huella de pesos, umbral, todos los tiempos/RSS (padre y encoder propio muestreados50ms), geometría del output y raw_sha256 están en video-presentation-summary.json. Los seis gates de procesamiento pasaron: máximos time_ratio1.030 y memory_ratio1.016; geometría y raw coinciden. La variación observada no demuestra una aceleración general. Se añade la reserva de cruce por separado y se agrega sin reemplazar las seis corridas.
SC-006/T077 sigue pendiente hasta completar también RSS del gateway, respuesta UI/health bajo carga real y coste separado de enrichment. Ninguna ausencia de estas medidas se convierte en PASS por disponer de un benchmark del detector.

## Regresión final de unidad/contrato y build
286 pruebas pytest PASS (67.44s),2avisos anteriores (AnyIO y ccache/Paddle);99 pruebas Vitest en43 archivos PASS (13.32s); TypeScript/Vite build PASS. Los cuatro casos focales de contratos/deadlines pasaron antes de la suite completa y las10 guardas de viewport/progreso/hook/conteo pasaron también.
Comandos: python -B -m pytest -o addopts='' -q; npm --prefix frontend run test; npm --prefix frontend run build. JSONSchema es una dependencia exclusiva de pruebas, añadida al extra dev y uv.lock; no se actualizaron los modelos ni dependencias de inferencia.
Las suites de navegador se distribuyen entre playwright.config.ts (114 casos previos en3tamaños) y playwright.008.config.ts (casos008); no se omite ningún archivo. El testIgnore de la suite anterior solo evita duplicar los seis archivos que la configuración008 ejecuta expresamente.

## Corrección descubierta en regresión
La limpieza de StrictMode retiraba src del reproductor sin reponerlo en su segundo montaje. Se reprodujo primero en rojo y se corrigió reponiendo la misma URL autorizada y abortando consultas de medio obsoletas; no se crea un job ni se descarga un Blob. Prueba focal2/2PASS y buildPASS. Los3 casos afectados de escritorio (rechazo nativo y dos recorridos de conteo) pasan (18.8s). Se reforzó la prueba de reproducción con readyState>=1 y medio decodificable en fixtures.
La primera pasada anterior quedó35PASS/3FAIL/76sin ejecutar; esos3fallos se resolvieron y los76restantes se ejecutan en tableta/móvil. No se cuentan casos omitidos como PASS ni se excluyen pruebas fallidas.

## Medidas finales de video y alcance de aceptación
Siete clips,3 pares AB/BA por clip (42brazos con detector/tracker real), todos los cuadros/FPS/tamaño preservados y raw idéntico por huella en cada par. Máximo cociente temporal completo1.030 y máximo cociente de RSS combinado1.016; quality_pass=true con jitter/IoU/lag del conjunto controlado. Presentación raw aislada también pasa por clip; se conservan todas las corridas en video-presentation-summary.json, sin descartar outliers.
Los pesos/umbral/dispositivo CPU configurados permanecieron iguales. Las seis corridas iniciales y la reserva adicional se realizaron consecutivamente; el informe conserva las huellas de ambos manifiestos. Solo el último subconjunto de presentación raw coincidió con el arranque de comprobaciones focales; su resultado es diagnóstico y no reemplaza el coste completo con modelos, que se midió sin esas suites. No se promete aceleración general.
Los modelos reales produjeron raw vacío en estas figuras sintéticas. Por tanto **T077/SC-006 permanece pendiente** de carga integrada representativa con vehículos elegibles, medición del gateway/UI/health y coste real del enriquecimiento por separado. No se acredita mayor precisión del detector ni del OCR.
**T079 permanece pendiente** de revisión humana completa. La inspección visual del agente y pruebas automáticas no constituyen aprobación humana ni certificación WCAG.

## Reproducción y privacidad
Playwright1.65.1/Chromium, Windows/CPU, viewports emulados360×800,768×1024,1440×1000 y texto200%; no son dispositivos físicos. El build final pasó después de corregir StrictMode. Regresión Vitest posterior:100/100 en43archivos (12.00s). Revisión de credenciales reales:1valor comprobado,0coincidencias en artefactos públicos y diff; detalles no sensibles en privacy-summary.json. Header de navegador/canario: managed-session.spec.ts.

## Navegador y cierre final
Regresiones previas:114 casos únicos verificados en3tamaños (35 de escritorio ya verdes,3 corregidos y repetidos PASS,76 de tableta/móvil PASS en4.9min). Suite008:44/45 iniciales PASS (1.7min); el caso de metadata de tableta leía dimensiones antes de loadedmetadata, se cambió a expect.poll sin relajar la condición y pasó aislado (11.7s). Total final159 casos únicos PASS tras resolver los fallos; no se cuentan los fallos iniciales como aprobaciones.
Zoom final:10escenas/3densas,50puntos por escena/escala,40operaciones por viewport. Error máximo0.02917px CSS; p95 máximo105.5ms; los tres viewports pasan los gates1px/200ms. Resultados en zoom-summary.json. Lista/ficha accede a61 resultados/3páginas, preserva track IDs y distingue evidencia de reproducción, con0POST/crops de imagen al consultar.
No se usa ejecución parcial como certificación: T077 y T079 siguen abiertos. La inspección visual del agente detectó y corrigió contraste del reproductor y barra final; falta el revisor humano. No se altera la política OCR ni se acredita precisión nueva.
Se restaura byte por byte el tsconfig.tsbuildinfo preexistente guardado antes del primer build. Sesiones históricas de métricas y cambios previos quedan fuera de los commits de implementación. Sin push, cambio de rama ni worktree nuevo.

## Ajuste rápido posterior: menú, espacio y recuperación
Solicitud posterior de interfaz: Imagen/Video se mueve a la cabecera; se retira el bloque visual de conexión y su reintento manual. Bootstrap automático con una solicitud simultánea, backoff2/4/8/16/30s, recuperación por online/visibilidad y nueva sesión tras vencimiento; no renueva evidencia anterior ni repite análisis. El modo elegido se conserva al cambiar el epoch y el reset explícito queda como icono de privacidad.
Contenedor hasta1920px con márgenes fluidos, escena prioritaria y ficha288px en escritorio; una columna hasta1100px. El mínimo de zoom es Ajustar, incluyendo cambios de tamaño, y el control Alejar se deshabilita allí. Se aclara que la hora mostrada corresponde a disponibilidad temporal en la vista.
103 pruebas Vitest PASS y build PASS. Comprobación aislada de navegador en360/768/1440 y texto100/200%: sin desborde horizontal, menú superior, sin bloque de conexión, mínimo de zoom estable; escena1076px/ficha288px en1440. Capturas sintéticas revisadas por agente, sin tocar servidores personales. T077/T079 mantienen su estado previo; no hay cambios del backend ni credenciales.

## Tarjeta de carga compacta
Miniatura y nombre agrupados en la columna de acciones, encima de Analizar/Limpiar; icono SVG de imagen y texto resumido. En escritorio la tarjeta seleccionada queda por debajo de200px; miniatura visible también tras analizar. Diseño de acciones adaptable a texto200% y móvil. Build PASS,3 pruebas focales de carga/política PASS y comprobación aislada360/768/1440 a100/200% sin desborde. Solo frontend; metadatos previos restaurados y backend intacto.
