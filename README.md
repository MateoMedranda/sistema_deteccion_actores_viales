# Sistema de detección de actores viales

Microservicio para analizar imágenes y videos viales con el modelo YOLOv10s aprobado. La API de
video registra un trabajo asíncrono, procesa los fotogramas, conserva las detecciones de forma
temporal y publica un MP4 anotado cuando concluye. Incluye conteo por línea, enriquecimiento de
atributos y placas e interfaz web. La iteración 006 incorpora exploración interactiva de imágenes;
cámara e historial permanente siguen fuera de alcance.

## Organización del proyecto

- `backend/`: API, gateway, pruebas Python, scripts, dependencias y configuración privada.
- `frontend/`: aplicación web, pruebas de interfaz y dependencias Node.
- `.specify/`, `.agents/`, `specs/` y `metricas/`: Speckit y documentación compartida en la raíz.

Arranque con el entorno existente, desde la raíz, en tres terminales:

```powershell
./backend/start.ps1 -Service api
```

```powershell
./backend/start.ps1 -Service gateway
```

```powershell
npm --prefix frontend run dev
```

Configura `backend/.env` y `backend/.env.web`. Para el Vite predeterminado, `WEB_ORIGIN=http://localhost:5173`; debe coincidir exactamente con la URL que abres. La API key permanece en el gateway, fuera del navegador.

El entorno `.venv/` existente se conserva para reutilizar los paquetes instalados. Una instalación nueva con `uv sync` desde `backend/` crea `backend/.venv/`; el script de arranque prefiere ese entorno si existe. Consulta [backend/README.md](backend/README.md).

Los comandos Speckit siguen ejecutándose desde la raíz con `SPECIFY_FEATURE_DIRECTORY=specs/009-video-progresivo`. Las referencias históricas a `app/`, `tests/`, `scripts/` y los archivos `.env` corresponden ahora a sus ubicaciones dentro de `backend/`.

## Configuración

Para una instalación nueva, ejecuta estos pasos desde `backend/`:

1. Use Python 3.12. Desde `backend/`, cree un entorno virtual.
2. Instale las dependencias: `uv sync --extra dev`.
3. Copie `.env.example` a `.env` y configure `MODEL_WEIGHTS_PATH` y `API_KEY` con valores privados.
4. Inicie el servicio: `uv run uvicorn app.main:app --reload`.

Para procesar video se requieren **FFmpeg y ffprobe 6 o superior** instalados y disponibles en
`PATH`; compruebe su instalación con `ffmpeg -version` y `ffprobe -version`. En Windows, instale
una distribución confiable, agregue su carpeta `bin` al `PATH` y reinicie la terminal. El servicio
acepta únicamente MP4/H.264 dentro de los límites declarados en `.env`; no cambie esos límites sin
medir memoria, latencia y cola.

La ruta de pesos debe apuntar al modelo aprobado. Si se requiere la variante local de Ultralytics
usada durante la investigación, configure `ULTRALYTICS_PATH` sin copiar sus fuentes ni sus pesos al
repositorio de este microservicio.

| Variable | Propósito | Regla de seguridad |
|----------|-----------|--------------------|
| `MODEL_WEIGHTS_PATH` | Archivo de pesos YOLOv10s aprobado | Ruta privada; no versionar ni publicar el archivo. |
| `ULTRALYTICS_PATH` | Variante local compatible, si se requiere | Debe ser una ruta controlada en el servidor. |
| `API_KEY` | Protege las rutas de análisis y artefactos | Usar un secreto largo, entregarlo por gestor de secretos y rotarlo. |
| `MODEL_CONFIDENCE_THRESHOLD` | Umbral entre 0 y 1 | Cambiarlo solo con evidencia de evaluación del modelo. |
| `MAX_UPLOAD_BYTES` y `MAX_IMAGE_PIXELS` | Límites de carga | Mantener límites conservadores en producción. |
| `ARTIFACT_TTL_SECONDS` | Vida de la imagen anotada | Reducirlo cuando la política de datos lo exija. |
| `MAX_CONCURRENT_INFERENCES` y `INFERENCE_DEVICE` | Protección de recursos | Ajustar según GPU/CPU documentada y memoria disponible. |

## Uso de la API

Envíe una imagen JPEG o PNG con una clave válida:

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/detections/images `
  -H "X-API-Key: $env:API_KEY" `
  -F "image=@C:\ruta\imagen.jpg"
```

La respuesta contiene las detecciones y una URL temporal protegida. Solicite esa URL con la misma
clave para ver la imagen anotada. Consulte el contrato completo en
`specs/001-deteccion-imagen-vial/contracts/openapi.yaml`.

### Video asíncrono

Envíe un MP4/H.264 con la misma clave. La respuesta `202` contiene un `job_id`; consulte su estado
hasta que sea `completed` y luego solicite las detecciones o el video anotado con esa misma clave.

```powershell
$headers = @{ "X-API-Key" = $env:API_KEY }
$job = curl.exe -s -X POST http://127.0.0.1:8000/api/v1/video-jobs `
  -H "X-API-Key: $env:API_KEY" -F "video=@C:\ruta\video.mp4" | ConvertFrom-Json
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/video-jobs/$($job.job_id)" -Headers $headers
```

Rutas disponibles al completar el trabajo: `GET /api/v1/video-jobs/{job_id}/detections`,
`GET /api/v1/video-jobs/{job_id}/summary` y
`GET /api/v1/video-jobs/{job_id}/annotated-video/content`. Los archivos de entrada y salida se
eliminan al vencer `VIDEO_RESULT_TTL_SECONDS` o al detener limpiamente el servicio.

## Seguridad y operación

- No registre ni comparta `API_KEY`, pesos del modelo o imágenes de usuarios.
- Despliegue detrás de TLS y un proxy con límites de solicitud.
- Los archivos y anotaciones se almacenan temporalmente y se eliminan al vencer el TTL.
- Ejecute `uv run --project backend pytest backend/tests` antes de entregar cambios.
- La procedencia aprobada del modelo es `yolov10s_best.pt` evaluado en
  `Vehicle_Detection_System`; cambiar pesos, clases o umbral exige una nueva evaluación.

## Interfaz de exploración de imágenes (006)

Con la API iniciada, desde otra terminal:

```powershell
Set-Location -LiteralPath './frontend'
npm ci
npm run dev -- --host 127.0.0.1
```

Con el gateway de008 configurado, selecciona JPEG/PNG y pulsa **Analizar imagen**. El flujo detecta y enriquece automáticamente. Selecciona un recuadro o su control equivalente en la lista para consultar atributos y recortes del vehículo y de la placa. Se utiliza **Detección N** para imagen estática; Track ID real en imágenes permanece como dependencia externa.

El original canónico PNG se obtiene mediante GET /api/v1/detections/{requestId}/original-image con la misma API key y propiedad que el análisis. La respuesta incluye original_image, source_expires_at y enrichment_eligible por detección. Original, anotación y resultados afectados usan Cache-Control: no-store. No hay endpoints nuevos de crop.

GET /health/enrichment-ready devuelve disponibilidad independiente de atributos, localización y OCR. Una disponibilidad parcial puede responder 503 en health y aun permitir enriquecimiento útil; una rama ausente no oculta las válidas. El janitor purga fuentes/resultados vencidos sin necesitar tráfico nuevo.

```powershell
uv run --project backend pytest backend/tests
npm --prefix frontend run build
npm --prefix frontend run test
Set-Location -LiteralPath './frontend'
npx playwright install chromium
npm run test:e2e
```

Playwright administra Vite 4173 y API sintética 8767, con almacenamiento temporal aislado. No reutiliza servidores personales ni necesita pesos privados para validar la UI. Las pruebas con modelos aprobados son independientes; consultar [validación 006](specs/006-mejoras-frontend/validation.md), [quickstart](specs/006-mejoras-frontend/quickstart.md) y [pendientes de usabilidad](specs/006-mejoras-frontend/usability.md).


La interfaz consulta GET /health/image-policy para mostrar los límites de archivo y píxeles configurados, sin cambiarlos. Original y anotación se recuperan independientemente sin repetir inferencia; rechazos de acceso retiran inmediatamente la evidencia. Los archivos temporales nuevos conservan recibos privados de vencimiento para purga tras reinicios; no se eliminan automáticamente ficheros históricos sin propiedad demostrable. Detalles y pruebas: [correcciones de convergencia](specs/006-mejoras-frontend/convergence-validation.md).

## Anotaciones despejadas y comparación de placas (007)

La exploración de imágenes ahora usa el original canónico, sin etiquetas numéricas sobre la escena. Los contornos distinguen13 clases con colores sólidos y una leyenda; foco, puntero y selección tienen formas diferenciadas. La banda externa identifica la detección contextual sin cambiar la ficha hasta activarla. La lista permite seleccionar vehículos pequeños por teclado o toque.

Una placa localizada permite comparar **Original** y **Procesada**, con ampliación1x/2x/4x dentro de la ficha. La versión visual aplica gris, contraste local y ampliación acotada; no reconstruye caracteres ni modifica la lectura. Cambiar de vista o ampliar no vuelve a ejecutar detección, localización ni OCR. La procedencia de lectura distingue intentos y variante seleccionada cuando el servicio los conoce.

El GET autenticado `/api/v1/enrichment-jobs/{enrichmentJobId}/detections/{detectionId}/plate-preview` devuelve PNG y la cabecera CORS `X-Plate-Preview-Metadata`. No acepta coordenadas ni recetas del cliente. Conserva dueño, no-store y menor TTL; usa una caché RAM acotada y un solo cálculo CPU real por proceso. Ante fallo visual sigue disponible el original autorizado; ante rechazo de acceso se retira la evidencia.

La lectura productiva conserva **baseline-v1**. La candidata de rescate y el evaluador están implementados, pero **todavía no se acredita mayor exactitud**: faltan referencias privadas verificadas y evaluación reservada. No se modificaron los modelos, pesos ni umbrales. Video y conteo mantienen sus flujos.

Consultar [guía007](specs/007-anotaciones-placas-legibles/quickstart.md), [validación](specs/007-anotaciones-placas-legibles/validation.md), [auditoría](specs/007-anotaciones-placas-legibles/audit.md) y [decisión de política](specs/007-anotaciones-placas-legibles/policy-decision.md). Los pendientes006 conservan su estado independiente.

## Exploración administrada de Imagen y Video (008)

La cabecera alterna espacios sin perder evidencia vigente. URL y credencial del backend se configuran únicamente en el servidor: copiar backend/.env.web.example a backend/.env.web, editar los valores localmente y conservar ese archivo fuera de Git. Nunca usar VITE_ para secretos. Cada gateway representa un principal del backend.

Desde raíz, terminal1: ./backend/start.ps1 -Service api.
Terminal2: npm --prefix frontend run build; después ./backend/start.ps1 -Service gateway -Port 4173.
Abrir http://127.0.0.1:4173 con WEB_ORIGIN configurado para ese origen. Desarrollo: gateway4174 y Vite4173; comandos en [quickstart008](specs/008-exploracion-imagen-video/quickstart.md).
Un despliegue remoto requiere HTTPS e ingreso privado autenticado existente; cookie/Origin no sustituyen esa autorización.

Imagen ofrece Ajustar,100/200/400% y recorrido local por arrastre o flechas. Video procesa una sola vez y consulta automáticamente atributos/placas elegibles, con progreso separado y reproducción disponible antes de terminar el enriquecimiento. Las cajas usan la paleta compartida sin rótulos; el suavizado solo afecta presentación y conserva raw/conteo.

Reanudar consulta recupera el mismo intento si se perdió la aceptación; Reintentar enriquecimiento tras fallo conocido conserva el video. Pausar/buscar/consultar fichas no inicia inferencias. La lista usa track IDs reales y páginas de25; i/fps identifica evidencia del video procesado, distinta del instante visible. La sesión tiene900s por defecto y nunca amplía la menor vigencia. Reiniciar retira ambos espacios y conserva la configuración del operador.

La selección directa en un contorno pausado queda para la [propuesta siguiente](specs/008-exploracion-imagen-video/propuesta-inspeccion-video.md). No se añaden recortes de video, historial ni políticas OCR. Resultados medidos, coste y pendientes: [validación008](specs/008-exploracion-imagen-video/validation.md).


## Video progresivo — iteración009

La interfaz permite explorar el video mientras se analiza: inicia con un prefijo confirmado de5s, bloquea avance pendiente y permite retroceder sin repetir modelos. Pausa y selecciona una caja/lista para consultar atributos, placa y recortes representativos que se enriquecen progresivamente. Análisis, enriquecimiento y exportación tienen estados independientes.

El frontend requiere WebCodecs/AVC compatible; si falta, informa incompatibilidad y conserva la consulta de datos. No muestra el video crudo como alternativa. Imágenes, exportación final y conteo conservan sus contratos. Node>=20.8.1; nuevas dependencias fijadas: av19.0.2 y mp4box2.6.0.

Ver [quickstart009](specs/009-video-progresivo/quickstart.md) y [validación efectiva](specs/009-video-progresivo/validation.md). La entrega funcional tiene pruebas automáticas; la comparación real larga fue diferida por el usuario y la prueba de cinco participantes sigue pendiente. Esto no acredita todavía todos los gates de rendimiento/usabilidad.
