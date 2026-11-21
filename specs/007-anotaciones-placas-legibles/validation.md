# Validación de implementación 007

Fecha:20 de noviembre2026, America/Guayaquil. Checkout principal y rama feature/007-anotaciones-placas-legibles. Sin commits ni staging automáticos. Los cambios previos se conservaron y los documentos/pruebas/fixtures de006 no se sustituyeron.

## Resultado

65 de70 tareas completadas. US1/US2/US3 implementadas y verificadas; US4 técnica implementada. Pendientes T061–T064 yT070: manifiesto privado con referencias independientes, reserva>=60(30 degradadas+30 controles), ejecución real, decisión y aceptación de exactitud.

La política activa sigue siendo baseline-v1. No se afirma mayor exactitud ni se promueve candidate-rescue-v1 con fixtures. Los pendientes históricos006/T067 y006/T068 conservan su estado.

## Línea base y entorno

Antes de los cambios:166 pruebas backend y52 frontend pasadas. Se verificaron ignore files y no se actualizaron dependencias/lockfiles, modelos/pesos/umbrales, autenticación ni configuración privada. Todos los servidores/almacenes de pruebas nuevos usan temporales aislados.

Windows11, Python3.12.15, AMD64 Family25 Model117 Stepping2 AuthenticAMD,16 CPUs lógicas y31.26GiB RAM. FastAPI0.115.14, Pydantic2.14.1, NumPy2.3.5, Pillow11.3, OpenCV-headless4.14.0.94, psutil7.2.2, pytest8.4.2. React18.3.1, TypeScript5.6.3, Vite5.4.21, Vitest2.1.9, Playwright1.65.1/Chromium. Inferencias de validación: adaptadores sintéticos, no modelos reales.

## Pruebas ejecutadas

| Comprobación | Resultado |
|---|---|
| pytest completo, sin cacheprovider, junit temporal |206 PASS,0 fallos,33.88s;4 avisos de dependencias/arnés |
| Casos adicionales de perfil (escala reducida, límites no uniformes, PNG limpio) |3 PASS; archivo de perfil completo7 PASS |
| Contrato/ref OpenAPI y acceso preview tras documentación de cabecera |Casos afectados PASS |
| Vitest final |75 PASS |
| TypeScript y Vite build |PASS |
| Playwright completo después de corregir carrera |114 PASS,0 fallos/omitidos/flaky,270.57s |
| Preview final después de limitar body/decode por metadata TTL |15 PASS,116.05s; tres viewports,30 comparaciones y30 solicitudes frías+30 calientes por viewport |
| Todas las identidades elegibles de10 escenas, teclado/toque |3 PASS,46.45s;360/768/1440 ytexto200% |

Comandos principales:

```powershell
& .venv/Scripts/python.exe tests/e2e/build_annotation_fixtures.py
& .venv/Scripts/python.exe -m pytest -o addopts='' -q -p no:cacheprovider --disable-warnings --junitxml=.pytest-tmp-007-backend/results.xml
npm --prefix frontend run test
npm --prefix frontend run build
# Desde frontend:
./node_modules/.bin/playwright.cmd test --reporter=json
./node_modules/.bin/playwright.cmd test image-analysis.plate-comparison.spec.ts image-analysis.plate-performance.spec.ts image-analysis.plate-states.spec.ts --reporter=json
./node_modules/.bin/playwright.cmd test image-analysis.unobstructed.spec.ts --reporter=json
```

El arnés usa únicamente puertos4173/8767, sin reutilizar servidores personales. Se conservaron las pruebas de imagen/video/conteo anteriores. Se adaptaron las expectativas de medios de006 al original y al contorno sin glifo; no se eliminó la ruta histórica de anotada.

## Evidencia US1/US2

Diez escenas sintéticas independientes, tres de28 detecciones, IDs de1/2/3 y más cifras, cajas pequeñas/superpuestas,13 clases y fallback. Original y anotada deliberadamente distintos, con texto incorporado en la anotada. Cero solicitudes de anotada desde el visor007; cero texto/glifos en la escena, incluso durante interacción. Contexto exterior con prioridad foco>puntero>selección; cada identidad elegible alcanzable y asociada por teclado/toque.

Registro explícito de colores, leyenda completa y elegibilidad exclusivamente del servidor. Selección doble, hover enfatizado, foco con halo y trazos auxiliares claros/oscuros sin relleno. La regresión de contraste mide estilos reales sobre blanco/negro, no solo constantes. Lista con alternativa>=44px. Texto200% sin scroll horizontal global; las columnas crecen con tipografía.

Latencia máxima de cambio de ficha con datos cargados: escritorio90.8ms, tablet106.8ms, móvil100.3ms, por reloj monotónico en la regresión completa.

## Evidencia US3 y recursos

Treinta comparaciones por viewport contra la API real de pruebas. Píxeles del original/ROI, identidad, PNG decodificado, metadata y CORS validados; GET de preview y modos/zoom no incrementan contadores de detector/atributos/localizador/OCR ni crean nuevos POST. Read/unreadable/failed localizados siguen inspeccionables; sin localización se declara indisponibilidad.

| Viewport | p95 frío | p95 caliente |
|---|---:|---:|
|1440|216.8ms|169.3ms|
|768|235.6ms|180.3ms|
|360|227.6ms|169.5ms|

Series de30 muestras cada una, caché vaciada mediante control exclusivo de pruebas para cada solicitud fría, p95 nearest-rank, desde activación hasta PNG correcto decodificado/renderizado. Todas las derivadas disponibles; ningún intento excedió10s. Estos tiempos son locales y sintéticos; no predicen rendimiento de todos los dispositivos.

CPU1, single-flight, cero cola para otras claves, deadline8s compartido no renovable y cupo retenido hasta finalizar el hilo real tras cancelación/timeout. Caché LRU8/16MiB, PNG2MiB, lado2048/producto2Mpx, TTL absoluto mínimo, sin archivos derivados. Reautorización antes de lectura, hits, publicación y respuesta. Health responde durante procesamiento bloqueado; consumidores abandonados no publican.

Purga real sin tráfico:1.007s. RSS del proceso durante ciclos: inicial795.32MiB, máximo796.22MiB, final796.21MiB. Incluye el proceso completo de pytest, no memoria exclusiva del preview. Ver [datos agregados](evidence-summary.json).

## Correcciones encontradas durante validación

Las pruebas de funciones/perfiles/cliente nuevos fallaron primero y pasaron después de implementar. Se congelaron decisiones y píxeles de baseline antes de extraer la política.

Una prueba adicional detectó que despachar una copia completa de estado desde un evento de contexto podía restaurar resultados anteriores. Se sustituyó por una acción específica aplicada dentro del reductor sobre estado vigente, con guarda de generación/fuente. Regresión en rojo->verde y suite completa114 PASS posterior.

Se añadió una guarda para que una caducidad más corta autenticada en metadata limite también cuerpo/decode, sin esperar el plazo inicial. Prueba de cuerpo suspendido en rojo->verde,75 Vitest y15 recorridos finales PASS. Fallos401/404/410 retiran evidencia inmediatamente; otros errores visuales conservan original autorizado.

Las métricas abarcan el resultado real de publicación, incluyendo rechazo tras transformación; no etiquetan completed un resultado vencido o abandonado.

## Procedencia y evaluación OCR

Provenance opcional normalizada antes de SQL/JSON/respuesta, bbox preservada ante fallo OCR, sin texto de candidatas descartadas. Imágenes usan baseline-v1 con intentos/ganador exactos; video conserva recorrido previo. used_enhancement sigue significando intento.

Candidata offline con dos recetas acotadas desde el mismo original, semáforos vigentes, presupuesto10s, conflictos=>sin texto, confianza observada sin sumas y sin ganador parcial al cortar. Evaluador probado con manifiestos sintéticos, fuga/duplicados/referencias faltantes, fallos en denominador, CER/normalización/gate y ausencia de datos sensibles en reporte/error. CLI y versiones/hashes preparados; lectura real NOT_RUN.

No se encontró manifiesto privado aprobado con referencias verificadas. No se generó evaluation-summary.json real ni se marcaron T061–T064/T070. [Decisión](policy-decision.md).

## Revisión visual y cierre

Revisadas capturas originales de escritorio/móvil y hojas de revisión con30 capturas sintéticas de escritorio/tablet/móvil: escena densa/200%, original/procesada, preparación/fallo/no aplicable, vacío/vencimiento y foco sobre blanco/negro. Se corrigió el apretado de las columnas al200%; identificadores completos, nombres legibles, controles accesibles y colores sólidos sin gradientes. Las hojas son recortes para inspección; los PNG completos se conservan en validation-assets.

No se declara certificación WCAG completa ni se sustituye la prueba humana de006. Matriz FR/SC e historias en [audit.md](audit.md). Rama confirmada y git diff --check sin errores de espacios. Índice sin cambios preparados; ningún reset, clean, stash, cambio de rama o commit.

Hook before_implement de métricas ejecutado con la selección confirmada gpt-6.1-sol/high. Hook after_implement opcional revisado; disponible como $speckit-metricas-cerrar, no ejecutado automáticamente.

## Correcciones T071-T075 verificadas (2026-11-21)

Evidencia actual posterior a la convergencia, conservando los registros anteriores: [convergence-evidence.json](convergence-evidence.json). Checkout principal en feature/007-anotaciones-placas-legibles; cambios previos conservados y sin commit automatico.

| Comprobacion | Resultado |
|---|---|
| Backend completo | 239 PASS, 0 fallos; 7 advertencias |
| Frontend Vitest | 78 PASS |
| TypeScript / Vite | PASS |
| Matriz completa de clases | 3 PASS, 360/768/1440 |
| Comparaciones y rendimiento de placas, API real | 6 PASS, 360/768/1440 |
| Otras regresiones de navegador de esta correccion | 24 PASS: escena, seleccion, convergencia, video y conteo |

**T071.** Resolucion, admision y reautorizacion bloqueantes salen del event loop a cuatro trabajadores de acceso acotados. Una senal notifica la terminacion: el sondeo frecuente inicial retrasaba I/O y fallo las metas de navegador; fue sustituido, sin relajar plazos ni aserciones. Se mantienen CPU1, single-flight, cero cola de computo para otras claves y deadline8s no renovable. El retiro usa un lock independiente de cache/SQLite; retiros y esperas vencidas no admiten computo ni publicacion tardios. Barreras sobre imagenes, store SQLite real y cache: health HTTP respondio en 2.9/2.9/3.2 ms mientras las barreras seguian retenidas, con liberacion de respaldo a400ms. Pasan desconexion, deadline y saturacion de cuatro accesos. Propietario/TTL/ROI se comprueban antes de lectura, hits, publicacion y entrega.

**T072.** Fabrica, entrada, muestreo, arranque parcial, salida y emision de metricas quedan dentro de la garantia de liberacion. Fallos entregan503 seguro, resuelven el Future, limpian sampler y no cachean evidencia; se admite una solicitud posterior. La emision se difiere hasta conocer el resultado atomico de publicacion, incluso si el llamador usa InferenceMetrics sin parametros especiales. Se conservo la regresion de vencimiento de006/T083.

**T073.** El visor recibe contexto explicito con prioridad foco>puntero>seleccion. Foco en lista enfatiza el contorno correcto sin mover foco ni cambiar ficha; color de clase y seleccion doble se conservan. Se prueban seleccion A/contexto B, blur/leave y reinicio de fuente/generacion. No se procesa por hover/foco.

**T074.** Las13 clases y fallback se verifican en escena/leyenda y, cuando son elegibles, lista/ficha. Las otras clases conservan contorno informativo sin ficha inventada. Se comprobo orden/subconjuntos, estilos efectivos y contraste de texto/trazos/foco sobre negro/blanco, seleccion/hover/foco, alternativa44px y texto100/200% en tres viewports. Son120 observaciones de estados de clases elegibles, mas el catalogo no elegible. Las seis capturas completas revisadas estan en validation-assets/convergence-*-classes.png. No se declara certificacion WCAG completa.

**T075.** EvaluationRun inmutable congela bytes del manifiesto, huellas de originales/perfiles/evaluador/pesos, parametros y entorno antes de inferir; conserva run_id privado y vincula pesos/diccionario OCR cargados. El resumen incluye OpenCV e identificacion del acelerador seleccionado sin divulgar run_id, rutas, placas o referencias. Pruebas unitarias y CLI controlado rechazan cambios de manifiesto, imagen, perfil, pesos y umbrales sin escribir un reporte nuevo ni promover candidatas.

| Viewport | p95 frio | p95 caliente | Maximo local |
|---|---:|---:|---:|
| desktop | 281.9 ms | 267.2 ms | 287.8 ms |
| tablet | 307.1 ms | 232.9 ms | 327.2 ms |
| mobile | 384.3 ms | 251.2 ms | 401 ms |

Por viewport:30 operaciones frias y30 calientes, reloj monotono desde seleccion hasta PNG correcto decodificado/renderizado; p95 nearest-rank muestra29. No se excluyeron fallos ni se aumento el presupuesto de2s/10s. Las30 comparaciones por viewport conservan ROI, metadata, identidad, CORS y contadores de modelos. Medios sinteticos autorizados con API real y adaptadores de prueba; no es una evaluacion OCR real.

Purga sin trafico:1.0201s. RSS de proceso: inicial797.52MiB, pico798.20MiB, final798.19MiB; no se atribuye memoria exclusiva a un job.

Comandos ejecutados desde el checkout principal:
```powershell
.venv/Scripts/python.exe -m pytest -o addopts='' -q --disable-warnings --basetemp=.pytest-tmp-007-convergence-approved --junitxml=.pytest-tmp-007-convergence-approved/backend.xml
# Desde frontend (Vitest/build verificados durante esta correccion):
npm run test
npm run build
./node_modules/.bin/playwright.cmd test image-analysis.classes.spec.ts --reporter=json
./node_modules/.bin/playwright.cmd test image-analysis.plate-comparison.spec.ts image-analysis.plate-performance.spec.ts --reporter=json
```

T071-T075 corregidas. T061-T064/T070 siguen pendientes de medios privados autorizados, referencias independientes y evaluacion reservada; aceptacion real NOT_RUN, baseline-v1 sin cambios.

## Corrección T076 verificada (2026-11-21)

El evaluador separa configuración solicitada, política de selección, inventario congelado y dispositivos efectivos observados. Se registra el inventario de las GPU disponibles antes de inferir aunque el detector esté configurado en CPU, porque el localizador conserva su selección automática. Cada llamada de detector/localizador vincula el dispositivo del predictor realmente inicializado; OCR se acredita con las configuraciones finales entregadas a la fábrica Paddle y las identidades de sus tres predictores. La captura respeta y restaura el hook CPU existente, sin mover modelos ni cambiar pesos, umbrales o configuración de producción.

Las observaciones se incorporan a una nueva instancia inmutable de EvaluationRun. El informe agrega dispositivo, identidad del acelerador y número de llamadas por etapa; distingue ejecutado, inicializado y no ejecutado, sin atribuir un dispositivo a un predictor perezoso que nunca se utilizó. Una discrepancia con la configuración, cambio de dispositivo/hardware, predictor reemplazado o procedencia no verificable invalida la corrida y evita emitir el informe. El rechazo queda retenido aunque el evaluador capture una excepción de una muestra.

Pruebas primero en rojo:8 fallos nuevos del contexto y5 del CLI. Después de implementar:32 pruebas enfocadas PASS y253 pruebas backend PASS,0 fallos y7 advertencias existentes. Se comprobaron CPU/CPU, detector CPU/localizador CUDA automático, dispositivos ausentes/no disponibles, discrepancias y cambios posteriores; el CLI conserva run_id y referencias privados y nunca promueve la candidata. Se verificó el hook anidado con la función CPU real del adaptador y fábricas controladas. Los escenarios CUDA usan adaptadores e inventario simulados; no se cargaron pesos ni se ejecutó inferencia sobre placas reales.

Comandos ejecutados desde el checkout principal:
```powershell
.venv/Scripts/python.exe -B -m pytest tests/unit/test_plate_evaluation_context.py tests/unit/test_plate_evaluation_cli_context.py tests/unit/test_plate_evaluation.py -q -o addopts='' --disable-warnings
.venv/Scripts/python.exe -B -m pytest -o addopts='' -q --disable-warnings --basetemp=.pytest-tmp-007-t076 --junitxml=.pytest-tmp-007-t076/results.xml
```

Datos agregados: [t076-evidence.json](t076-evidence.json). El frontend y los cambios previos se conservan; T076 afecta exclusivamente al evaluador offline, sus pruebas y esta documentación. T061–T064/T070 continúan pendientes, exactitud real NOT_RUN y baseline-v1 activa. No se generó evaluation-summary.json real ni se creó un commit automático.
