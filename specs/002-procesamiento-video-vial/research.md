# Research: Procesamiento vial por video

## Cola temporal persistente

- **Decision**: Usar SQLite local para la cola y estado temporal de trabajos, junto con un trabajador interno iniciado por el ciclo de vida del servicio. Al iniciar, cualquier trabajo `processing` no vencido se devuelve a `queued` de forma atómica.
- **Rationale**: Satisface recuperación tras reinicio y no añade un servicio distribuido para el alcance académico. El TTL evita que SQLite se convierta en historial.
- **Alternatives considered**: Tareas en memoria se descartaron porque se pierden al reiniciar; una cola externa se aplaza porque añade infraestructura no requerida por el alcance actual.

## Sondeo y codificación de video

- **Decision**: Usar FFmpeg/ffprobe como dependencia de ejecución para validar contenedor/códec, leer fotogramas y codificar el resultado MP4/H.264.
- **Rationale**: Permite distinguir el MIME declarado del códec real, aplicar el perfil de video y producir una salida reproducible compatible con MP4/H.264.
- **Alternatives considered**: Confiar solo en extensión o MIME se descarta por seguridad; usar únicamente el lector de OpenCV se descarta porque expone menos información fiable de códec y puede variar entre plataformas.

## Rastreo de actores

- **Decision**: Usar ByteTrack como rastreador de referencia con el modelo YOLOv10s cargado una vez. El estado de seguimiento se reinicia entre trabajos y persiste dentro de cada video.
- **Rationale**: Equilibra continuidad de `track_id`, costo computacional y soporte de escenas viales sin un modelo extra de apariencia.
- **Alternatives considered**: Asociación por IoU/centro se descarta por cambios frecuentes de ID; BoT-SORT queda para una comparación futura, no para esta iteración.

## Autenticación antes de carga

- **Decision**: Validar la API key en middleware específico de carga antes de delegar la solicitud al análisis multipart. La autenticación devuelve un principal con `key_id`; trabajos y artefactos se filtran por ese identificador.
- **Rationale**: Evita aceptar o almacenar el cuerpo de un video no autorizado y permite aislar recursos de distintas credenciales. La configuración mantiene compatibilidad con la API key única previa mediante un `key_id` predeterminado.
- **Alternatives considered**: Un `Depends` de ruta se descarta porque el cuerpo multipart puede ser analizado antes de ejecutar la dependencia; usar un único propietario global no satisface el aislamiento entre credenciales.

## Cancelación, timeout y limpieza

- **Decision**: La cancelación y el timeout son cooperativos: el trabajador verifica ambas condiciones antes de cada fotograma y antes de publicar la salida. La entrada se elimina en todo estado terminal; salida y metadatos de completados viven 60 minutos.
- **Rationale**: Evita artefactos parciales y permite detener de forma segura librerías de visión que no se pueden interrumpir en mitad de una inferencia.
- **Alternatives considered**: Interrumpir un hilo en mitad de una llamada nativa se descarta por riesgo de corrupción; conservar entradas después de completar se descarta por minimización de datos.

## Resultado y observabilidad

- **Decision**: Exponer un resumen y URL temporal en la consulta principal; el detalle de detecciones se pagina por fotograma. Registrar tiempos de carga, validación, fotograma, inferencia, anotación y salida; memoria de proceso, errores, versión de modelo, FFmpeg y configuración no secreta.
- **Rationale**: Evita respuestas enormes y permite auditar rendimiento sin revelar rutas, credenciales ni contenido de video.
- **Alternatives considered**: Incluir todas las detecciones en una respuesta se descarta por tamaño; registrar solo tiempo total se descarta porque no permite diagnosticar cuellos de botella.
