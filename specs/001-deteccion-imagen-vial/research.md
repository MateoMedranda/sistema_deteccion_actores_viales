# Research: Detección vial en imagen

## Decision 1: Reutilizar YOLOv10s solo para detección primaria

**Decision**: Adaptar el detector que utiliza `weights/yolov10s_best.pt` del proyecto de
investigación `Vehicle_Detection_System` como una implementación detrás de un contrato de detector.
Solo se expondrán clase, confianza y cajas; los módulos de atributos y ALPR quedan excluidos.

**Rationale**: El repositorio de investigación identifica YOLOv10s como el modelo de mejor
rendimiento y ya expone los datos requeridos por la especificación: `bbox`, `confidence`,
`class_id` y `class_name`. Esto preserva la línea base evaluada y evita alterar la calidad con otro
modelo durante la primera iteración.

**Alternatives considered**:

- Reutilizar la aplicación Tkinter completa: rechazada porque mezcla selección local de archivos,
  inferencia, exportación y visualización, y no ofrece un contrato para una interfaz cliente.
- Ejecutar la cascada de atributos y placas: rechazada porque contradice el alcance y aumenta el
  tratamiento de datos sensibles.
- Elegir un modelo distinto: rechazado porque no aporta evidencia de mejora frente al modelo ya
  comparado.

## Decision 2: Recibir una imagen con carga de archivo controlada

**Decision**: Aceptar una única carga multipart y procesarla como archivo con respaldo temporal;
validar tamaño antes de leer por completo, MIME permitido, decodificación y número de píxeles.

**Rationale**: La documentación oficial de FastAPI indica que `UploadFile` usa un archivo temporal
con desbordamiento a disco y evita cargar archivos grandes íntegramente en memoria. La validación de
contenido, además del MIME declarado, cumple la constitución al tratar la entrada como no confiable.

**Alternatives considered**:

- Recibir el contenido íntegro como bytes: rechazado por mayor riesgo de consumo de memoria.
- Aceptar URL remota: rechazado porque introduce SSRF y no es necesario para la primera iteración.
- Aceptar varios archivos: rechazado porque la especificación limita el análisis a una imagen.

## Decision 3: Separar metadatos y visualización anotada

**Decision**: La operación de análisis devuelve metadatos estructurados, detecciones y una URL de
artefacto temporal. Una segunda operación protegida entrega la imagen anotada mientras esté vigente.

**Rationale**: La separación evita incorporar una imagen codificada dentro de cada respuesta de
metadatos, mantiene el contrato fácil de consumir por una interfaz y permite eliminar el artefacto
tras un TTL corto. La visualización contiene cajas, clase y confianza, como exige la especificación.

**Alternatives considered**:

- Incluir la imagen en Base64 dentro de la respuesta: rechazada porque incrementa tamaño, memoria y
  latencia.
- Guardar imágenes indefinidamente: rechazada por el requisito de no mantener historial.
- No entregar visualización anotada: rechazada porque incumple FR-005.

## Decision 4: Cargar el modelo en el ciclo de vida del servicio

**Decision**: Inicializar los pesos una vez al iniciar el proceso y mantener el adaptador disponible
como estado de la aplicación. La ruta de análisis solo solicita inferencia al adaptador ya listo.

**Rationale**: FastAPI ofrece un ciclo de vida de aplicación para recursos compartidos; esta elección
evita repetir una carga costosa por solicitud y satisface FR-010 y el objetivo de latencia. La
lectura de pesos, umbrales y dispositivo se realizará desde configuración tipada de entorno.

**Alternatives considered**:

- Cargar el modelo por solicitud: rechazado por latencia, uso de memoria y FR-010.
- Usar variables globales sin ciclo de vida: rechazado porque dificulta pruebas, cierre ordenado y
  manejo de fallos de inicialización.

## Decision 5: Autorización simple, medible y externa al código

**Decision**: Proteger los recursos de análisis y artefactos con una clave de API configurada en
entorno; comparar la clave de forma segura y no registrar el valor. El despliegue productivo debe
usar TLS y un proxy que aplique límites de solicitud.

**Rationale**: La especificación solicita usuarios autorizados y la constitución exige autenticación
antes de aceptar o exponer resultados. Una clave de API permite demostrar ese control sin introducir
gestión de usuarios, persistencia o identidad fuera del alcance.

**Alternatives considered**:

- Rutas públicas: rechazadas porque incumplen la constitución.
- Usuarios y contraseñas propios: rechazados porque agregan persistencia, recuperación de cuentas y
  riesgos que no son necesarios para la primera iteración.
- OAuth completo: aplazado para una integración futura con la interfaz o un proveedor institucional.

## Decision 6: Pruebas aisladas y evidencia de rendimiento

**Decision**: Usar dobles para el detector en pruebas unitarias y de rutas, conservar un conjunto
pequeño y autorizado de imágenes de referencia para pruebas de extremo a extremo y medir tiempos
con el modelo real en el hardware documentado.

**Rationale**: Las pruebas rápidas no dependen de GPU ni de pesos; las pruebas de referencia validan
el contrato, anotación y rendimiento sin convertir cada prueba en un benchmark costoso.

**Alternatives considered**:

- Usar el modelo real en todas las pruebas: rechazado por lentitud, variabilidad de hardware y
  dificultad de reproducción.
- Omitir pruebas de rendimiento: rechazado por SC-001 y la constitución.

## Sources consulted

- FastAPI, [Request Files](https://fastapi.tiangolo.com/tutorial/request-files/): cargas de archivo,
  `UploadFile` y comportamiento temporal.
- FastAPI, [Lifespan Events](https://fastapi.tiangolo.com/advanced/events/): inicialización y cierre
  de recursos compartidos de aplicación.
- Ultralytics, [Predict Mode](https://docs.ultralytics.com/modes/predict): resultados de detección,
  cajas, confianza, clases y visualización anotada.
- Implementación local de investigación: `Vehicle_Detection_System/core/yolov10_detector.py` y
  `Vehicle_Detection_System/system_utils/drawing.py`.
