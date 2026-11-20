# Quickstart y validación — 006

**Estado**: guía para la futura implementación. Los archivos de prueba nuevos y las extensiones de API aún no existen en el producto; esta planificación no acredita ejecución satisfactoria.

## Entorno

- Continuar en `codex/006-mejoras-frontend`, con los cambios de backend ya confirmados preservados.
- Python >=3.12, uv y dependencias del proyecto; Node/npm compatibles con el lockfile existente.
- Configuración privada del servicio, clave de sesión y pesos/manifiestos aprobados para comprobación real. Nunca copiar credenciales a comandos de documentación ni al frontend.
- FFmpeg/ffprobe para regresión de video; medios de prueba autorizados. Para casos deterministas, usar adaptadores de prueba existentes, no servicios o datos de personas sin autorización.

## Iniciar tras implementar

Desde la raíz del checkout activo:

```powershell
uv sync --extra dev
uv run uvicorn app.main:app --reload
```

En otra terminal desde esa misma raíz:

```powershell
Set-Location -LiteralPath './frontend'
npm ci
npm run dev -- --host 127.0.0.1
```

Si faltan `.env` o recursos locales al trasladar el checkout, usar la configuración privada existente del checkout principal; no recuperar secretos copiándolos a Git. Revisar los orígenes CORS permitidos. Escribir la credencial solo en el control de sesión de la interfaz.

## Secuencia funcional

1. Cargar una imagen controlada con varios vehículos y pulsar una sola vez «Analizar imagen».
2. Comprobar etapas de detección y enriquecimiento automático; selección disponible durante la espera, sin dos botones manuales de imagen ni porcentajes inventados.
3. Mover puntero sobre un recuadro: cursor y énfasis visibles. Seleccionar y comparar identificador, clase, confianza y ficha.
4. Confirmar que el recorte del vehículo y de placa corresponden a la misma detección. Repetir con placa localizada ilegible, placa ausente y fallo de OCR.
5. Cambiar selección usando lista y teclado. En cajas superpuestas, todos los vehículos deben seguir accesibles mediante la lista.
6. Probar imagen EXIF rotada/reflejada y cajas al borde; comparar el original canónico, anotación y crop. Nunca tratar detection_id como Track ID.
7. Simular fallo solo de enriquecimiento y reintentar: detección no se repite, datos básicos permanecen.
8. Reiniciar durante carga/procesamiento y cambiar credencial/base con respuestas tardías: ningún resultado anterior reaparece. El reset no espera cancelación para limpiar.
9. Dejar vencer una fuente sin realizar peticiones: el janitor debe purgar originales/resultados en <=2 s; posterior lectura del dueño devuelve 410, ajeno 404.
10. Completar video, enriquecimiento de video y conteo existentes, incluyendo cancelación y reset; no exigir el rediseño de video futuro.

## Comprobaciones de backend

Añadir pruebas con estos destinos durante implementación; los comandos son el objetivo de ejecución posterior, no una afirmación de que ya existen:

```powershell
uv run pytest tests/unit/test_image_geometry.py tests/unit/test_image_validation.py tests/unit/test_enrichment_job_store.py tests/unit/test_enrichment_core.py
uv run pytest tests/integration/test_canonical_image_access.py tests/integration/test_enrichment_readiness.py tests/integration/test_enrichment_job_routes.py tests/integration/test_enrichment_lifecycle.py
uv run pytest tests/contract/test_detection_contract.py tests/contract/test_openapi_contract.py tests/integration/test_cors.py
uv run pytest tests/e2e/test_image_and_video_regression.py tests/e2e/test_line_counting_regression.py
```

- Geometría: orientaciones EXIF 1–8, dimensiones canónicas, cajas fuera de rango/degeneradas, identidad sin renumeración por clase y recorte de placa relativo al vehículo.
- Acceso: credencial inválida, dueño/ajeno, desconocido/vencido, no-store y cero rutas privadas en respuesta.
- Readiness: sin modelos y cada combinación de atributos/localización/OCR; localización disponible con lector ausente conserva evidencia válida.
- Saneamiento: estado no read con texto inyectado por fixture no debe aparecer en JSON, tablas ni respuesta.
- Concurrencia: barreras y reloj controlado para cancel/finish, TTL/finish y purga sin tráfico; no sleeps largos ni inferencia real para probar carreras.
- Modelos: ejecutar además comprobaciones con medios autorizados y configuración real; comparar normalización con línea base aprobada y registrar diferencias. Una suite con adaptadores deterministas no certifica la precisión de detección u OCR.

Al cerrar implementación, ejecutar la suite completa pertinente con `uv run pytest`; si una prueba depende de recursos privados ausentes, registrar el motivo y no declarar validación real completada.

## Comprobaciones de frontend

Desde `frontend/`, después de crear las pruebas y configuración previstas:

```powershell
npm run build
npm run test
npx playwright install chromium
npm run test:e2e
```

- Unitarias de geometría con cuadrantes de colores, selección/reducer, generación, abort, polling, recursos, >50 resultados y desorden.
- Componentes: Enter/Espacio/toque, lista equivalente, foco estable, recorte de placa ilegible, estados independientes y errores seguros.
- Integración determinista con servidor de pruebas y adaptadores de prueba; no introducir mocks en el flujo de producción.
- Capturas en 360/768/1440 de todos los estados. Revisar la primera referencia visual antes de aprobarla y generar/comparar en el mismo entorno.
- Inspeccionar contraste, objetivos 44x44, texto 200%, orden de foco y movimiento reducido. No inferir conformidad WCAG total de una captura o una prueba DOM.

## Evidencia y aceptación

Registrar resultados en la documentación de validación de 006 durante implementación: commit, versiones, dispositivo/viewport, medios y configuración no sensible, pruebas ejecutadas y resultado; enlaces de evidencia sin placas ni secretos. Medir ficha <1 s con datos cargados y limpieza <=2 s bajo las condiciones descritas.

SC-007 requiere evaluación con 5 personas: >=4 completan el recorrido sin ayuda y califican claridad/presentación >=4/5. Si aún no se realiza, se declara pendiente; no sustituirla por una opinión del agente ni por snapshots.

Esta guía, el [modelo de datos](data-model.md), el [contrato frontend](contracts/frontend-interactions.md) y el [contrato backend](contracts/backend-additions.md) deben convertirse en tareas trazables con `$speckit-tasks` antes de implementar.
