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
