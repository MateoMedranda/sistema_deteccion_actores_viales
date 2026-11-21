# Uso y validación — 007

Trabajar en el checkout principal, rama feature/007-anotaciones-placas-legibles. No recrear la rama ni usar reset/clean/stash. Se conservan dependencias, modelos, pesos, umbrales y autenticación existentes.

## Explorar imágenes

Con el backend y el frontend iniciados según README, configurar la sesión y pulsar **Analizar imagen**. Se ejecuta detección y enriquecimiento en una acción.

La escena utiliza el original canónico, con contornos de clase y sin números superpuestos. Pasar el puntero o enfocar un control cambia únicamente la banda externa. Clic, Enter, Espacio o toque seleccionan el vehículo. La lista ofrece controles grandes para las cajas pequeñas o superpuestas. La leyenda incluye actores que no admiten enriquecimiento; el color no decide su elegibilidad.

Si falta el original se muestra indisponibilidad y **Reintentar original**. La lista y los datos autorizados siguen disponibles. No se usa la imagen anotada como sustituto. Las rutas históricas y video/conteo se conservan.

## Comparar placas

Al seleccionar una placa localizada se prepara automáticamente una derivada, incluso si la lectura es ilegible o falló. **Original** es la vista inicial. **Procesada** muestra gris, contraste local y ampliación cuando corresponde. Los controles 1x/2x/4x amplían dentro de la región; la región admite foco y desplazamiento por teclado.

Cambiar de vista o ampliar no ejecuta modelos ni nuevas solicitudes. Reintentar la versión procesada solo repite su GET, sin nuevo análisis. La procedencia de lectura y los intentos son independientes del tratamiento mostrado. Ampliar no recupera información ausente.

El GET protegido es:
`/api/v1/enrichment-jobs/{enrichmentJobId}/detections/{detectionId}/plate-preview?profile=display-contrast-v1`.

Devuelve PNG y X-Plate-Preview-Metadata (JSON ASCII <=2048 bytes), con no-store. CORS expone esa cabecera. El cliente valida identidad, ROI, perfil, vigencia, bytes y dimensiones. 401/404/410 retiran evidencia afectada; los fallos de tratamiento conservan el original vigente. 422 significa no aplicable; 429 indica cupo ocupado y permite reintentar. El intento local completo tiene un máximo de 10 s.

Límites: un cálculo real por proceso, single-flight para la misma clave, sin cola de otras claves; servidor 8 s, caché RAM LRU de 8 entradas/16 MiB, PNG <=2 MiB, lado <=2048 y <=2 millones de píxeles. Nunca se amplía el TTL original/trabajo. Reset, selección, credencial, fuente, trabajo y caducidad abortan o invalidan la evidencia anterior.

## Pruebas

Usar los entornos existentes; no instalar versiones nuevas para validar.

```powershell
& .venv/Scripts/python.exe tests/e2e/build_annotation_fixtures.py
& .venv/Scripts/python.exe -m pytest -o addopts='' -q --disable-warnings
npm --prefix frontend run test
npm --prefix frontend run build
npm --prefix frontend run test:e2e
```

Playwright usa exclusivamente Vite4173 y API8767 con TemporaryDirectory y adaptadores sintéticos contados. No reutiliza servidores personales. Los controles de caché/contadores solo existen en tests/e2e/serve_frontend_test_api.py; no se agregan a la aplicación productiva.

Resultados, condiciones y capturas: [validation.md](validation.md), [audit.md](audit.md). La presentación y el rendimiento sintéticos no prueban mayor exactitud de OCR ni cierran los pendientes de006.

## Evaluar exactitud real

La política activa sigue siendo baseline-v1. candidate-rescue-v1 solo está disponible en el evaluador offline. No hay selector de interfaz ni petición que la active.

Crear el manifiesto fuera del repositorio conforme a [evaluation-protocol.md](evaluation-protocol.md). Debe contener version=1, associations_frozen=true, reference_independent=true y samples. Cada muestra contiene id, split (adjust/test), group_id, scene_id, image (ruta privada), detection_id, vehicle_bbox (cuatro enteros del original canónico), reference, reference_verified=true, verification_source y stratum (degraded/control). Referencias verificadas de forma independiente; separar escenas/grupos/imágenes entre ajuste y reserva. Reserva mínima:60, incluidas30 degradadas y30 controles. El evaluador usa las detecciones/localizaciones producidas, no recortes perfectos de referencia.

```powershell
$plateManifest = Read-Host 'Manifiesto privado autorizado'
& .venv/Scripts/python.exe scripts/evaluate_plate_profiles.py --manifest $plateManifest --baseline baseline-v1 --candidate candidate-rescue-v1 --output specs/007-anotaciones-placas-legibles/evaluation-summary.json
```

El reporte es agregado, sin textos, imágenes, identidades por placa, credenciales ni rutas privadas. Registra huellas, versiones, condiciones, denominadores, CER, lecturas falsas y coste. El CLI no promueve políticas. Una promoción requiere revisar el gate y cambiar explícitamente la composición, con regresiones.

Sin referencias reales, T061–T064 y T070 permanecen pendientes. No crear un reporte PASS con fixtures. Se mantienen los pendientes históricos 006/T067 y006/T068.
