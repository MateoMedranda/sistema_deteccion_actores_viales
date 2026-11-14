# Research: Conteo de actores por línea

## Trabajo de conteo asíncrono

- **Decision**: Crear un trabajo temporal de conteo separado y publicable por progreso.
- **Rationale**: La futura UI puede consultar totales acumulados después de cada cruce sin bloquear al usuario mientras se genera el resultado visual.
- **Alternatives considered**: Cálculo síncrono se descarta por bloquear videos largos; devolver solo el total final se descarta porque no permite actualización progresiva.

## Geometría de cruce

- **Decision**: Usar el centro de la caja delimitadora y el signo del producto cruzado respecto al segmento orientado A→B.
- **Rationale**: Es independiente de la resolución, funciona con líneas diagonales y evita contar solo porque una esquina de la caja toca la línea.
- **Alternatives considered**: Cualquier intersección de caja se descarta por falsos positivos; la base de la caja se aplaza porque requiere una definición distinta por clase y cámara.

## Deduplicación y sentido

- **Decision**: Contar una vez cada par count_job_id/track_id y fijar el sentido al primer cambio válido de lado.
- **Rationale**: Impide duplicados por oscilación alrededor de la línea sin prometer identidad física cuando un rastreador reasigna IDs.
- **Alternatives considered**: Contar cada cruce se descarta por sobreconteo; entrada/salida se descarta porque depende de la orientación de la cámara.

## Video anotado de conteo

- **Decision**: Reutilizar el video anotado temporal y detecciones persistidas del trabajo de video como entrada; superponer línea, direcciones y totales.
- **Rationale**: Cumple la prohibición de volver a ejecutar detección y conserva evidencia visual verificable.
- **Alternatives considered**: Reprocesar el video original se descarta por costo y porque el original se elimina al finalizar; devolver solo JSON se descarta por falta de evidencia visual.

## Expiración y fallos

- **Decision**: El conteo no puede vivir más que su video origen; al expirar la fuente se eliminan configuración, eventos y artefactos de conteo.
- **Rationale**: Mantiene minimización de datos y evita resultados sin evidencia de origen.
- **Alternatives considered**: Historial permanente se descarta por alcance y constitución.

