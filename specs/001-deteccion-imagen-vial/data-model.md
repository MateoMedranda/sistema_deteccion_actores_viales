# Data Model: Detección vial en imagen

## Solicitud de análisis

Representa una operación individual de análisis de una imagen.

| Campo | Tipo conceptual | Reglas de validación |
|-------|-----------------|----------------------|
| `request_id` | Identificador único | Se genera en el servicio; nunca se acepta desde el cliente. |
| `submitted_at` | Fecha y hora | Se registra al aceptar la solicitud. |
| `status` | Estado | `received`, `validated`, `processing`, `completed`, `rejected` o `failed`. |
| `processing_time_ms` | Entero no negativo | Se completa solo al finalizar o fallar el análisis. |
| `error_code` | Texto opcional | Usa códigos públicos; nunca incluye trazas, secretos ni rutas. |

**Transiciones**:

```text
received -> validated -> processing -> completed
received -> rejected
validated -> failed
processing -> failed
```

No se persiste esta entidad después de la retención temporal necesaria para servir la imagen
anotada y los logs operativos.

## Imagen enviada

Representa el archivo temporal proporcionado por el usuario.

| Campo | Tipo conceptual | Reglas de validación |
|-------|-----------------|----------------------|
| `original_filename` | Texto opcional | Se trata como metadato no confiable; no se utiliza como ruta. |
| `media_type` | Texto | Solo `image/jpeg` o `image/png` después de validar el contenido. |
| `size_bytes` | Entero positivo | Debe ser menor o igual al límite configurable inicial de 10 MiB. |
| `width`, `height` | Enteros positivos | El producto no puede superar 16 megapíxeles por defecto. |
| `temporary_path` | Referencia privada | Se genera con identificador aleatorio dentro del directorio temporal configurado. |

La imagen se elimina ante rechazo, error o vencimiento de su artefacto asociado.

## Detección vial

Representa un actor vial encontrado por el modelo aprobado.

| Campo | Tipo conceptual | Reglas de validación |
|-------|-----------------|----------------------|
| `detection_id` | Entero | Secuencial solo dentro de una solicitud. |
| `class_id` | Entero | Corresponde a una clase publicada por el modelo cargado. |
| `class_name` | Texto | Proviene del mapa de clases del modelo; se publica como etiqueta legible. |
| `confidence` | Decimal | Valor entre 0 y 1, redondeado solo para presentación. |
| `bbox` | Caja rectangular | Incluye `x_min`, `y_min`, `x_max`, `y_max`; queda dentro de los límites de la imagen. |

Una solicitud completada puede tener cero o más detecciones. Cero detecciones es un resultado válido,
no un error.

## Artefacto anotado temporal

Representa la imagen con cajas, clase y confianza superpuestas.

| Campo | Tipo conceptual | Reglas de validación |
|-------|-----------------|----------------------|
| `artifact_id` | Identificador único | No contiene nombre original ni información personal. |
| `request_id` | Referencia | Se asocia exactamente a una solicitud de análisis completada. |
| `media_type` | Texto | `image/jpeg` para la primera iteración. |
| `expires_at` | Fecha y hora | Vence por defecto 15 minutos después de completarse. |
| `temporary_path` | Referencia privada | No se expone en las respuestas. |

El artefacto se obtiene mediante una URL protegida y se elimina al vencimiento o durante la limpieza
ordenada del servicio.

## Configuración de servicio

| Campo | Origen | Regla |
|-------|--------|-------|
| Ruta de pesos del modelo | Variable de entorno | Obligatoria al iniciar; la aplicación no queda lista sin ella. |
| Umbral de confianza | Variable de entorno | Debe estar entre 0 y 1; su valor y versión de modelo se registran en métricas. |
| Dispositivo de inferencia | Variable de entorno | Se valida al iniciar; puede referir CPU o el acelerador disponible. |
| Clave de API | Almacén de secretos o variable de entorno local | Obligatoria fuera de pruebas; no se registra ni se publica. |
| Límites de carga y TTL | Variable de entorno | Valores positivos y documentados; los cambios se reflejan en la documentación de operación. |
