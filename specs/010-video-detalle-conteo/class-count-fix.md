# Corrección del catálogo multiclase — 2026-11-25

Revisión solicitada tras observar que el contador parecía sumar solo automóviles. Se conserva feature/010-video-detalle-conteo y el checkout principal. Corrección posterior al cierre de las 74 tareas, trazada a FR-010/FR-017, SC-004/SC-006 y T034–T058; no se sustituye la evidencia histórica de cierre.

## Causa comprobada

El checkpoint configurado yolov10s_best.pt contiene exactamente Car, Bus, Truck, Big Truck, Motorbike y Van. La taxonomía anterior aceptaba truck y motorcycle, pero no big truck ni motorbike. `is_vehicle` excluía estas dos clases del cruce y de la inspección; la presentación las trataba como desconocidas y el resumen las marcaba para revisar. No era un filtro explícito de «solo auto».

La regresión con las seis clases, dos mediciones reales a lados opuestos del segmento y un cuadro predicho intermedio, contabilizaba 4 en lugar de 6 antes de la corrección. También fallaban la elegibilidad de Big Truck/Motorbike y los recortes de camión pesado (cinco fallos iniciales).

Truck y Van ya eran elegibles: no se atribuye su ausencia concreta al mismo fallo. El modelo real detectó Truck y Van en seis muestras breves del video previamente autorizado. Agregado de observaciones: Car=72, Big Truck=3, Van=4, Truck=1. Son observaciones de cuadros independientes, no cantidades únicas ni precisión medida. Bus/Motorbike no aparecieron en esas muestras. Los últimos trabajos habían retirado sus observaciones por TTL; no se puede afirmar qué cruce concreto faltó en ellos. Evidencia sin imágenes, placas ni rutas de medios: [model-class-diagnostic.json](evidence/model-class-diagnostic.json).

## Cambio y límites

Registro compartido backend/frontend: Big Truck → big_truck, etiqueta Camión pesado y color propio; Motorbike → motorcycle, etiqueta Motocicleta. Truck permanece Camión y Van permanece Furgoneta. Se conservan los 13 colores originales y se añade uno para camión pesado. Los nombres e IDs originales del detector permanecen en las observaciones.

El filtro de enriquecimiento reconoce las grafías equivalentes y, si se habilita truck, también su subtipo pesado. Habilitar únicamente car sigue excluyendo los demás grupos; habilitar solo big_truck no habilita truck. Esto evita que el contador reconozca un camión cuyo recorte luego rechace el filtro legacy. No cambia pesos, umbral, intervalo, hilos ni .env privado.

Continúa la política geométrica: el centro medido debe atravesar el segmento finito siguiendo la flecha; pasar cerca, tocar sin confirmar, cruzar una prolongación o circular en sentido inverso no suma. La predicción intermedia no aporta votos/cruces. El resumen de todo el video es independiente: una clase observada puede figurar allí aunque no cruce la línea. Se conservan personas excluidas y clases desconocidas explícitas para revisión.

No se reescriben eventos históricos ni se modifican las bases privadas. Reiniciar la API/gateway, recargar el frontend y ejecutar un análisis nuevo regenera consistentemente los agregados. Si aún falta una furgoneta concreta, revisar su clase medida, continuidad del Track ID, cruce del centro y sentido; este parche no acredita la exactitud global del modelo ni corrige pérdidas de seguimiento por sí mismo.

## Validación

- Suite backend completa con las primeras 12 regresiones: 458 aprobadas, sin errores/omitidos. Luego se añaden y verifican las diez comprobaciones restantes: archivo final de 22 regresiones aprobado. Total de pruebas distintas verificadas: 468.
- ByteTrack real con detector sintético de seis clases, orden alternado e intervalos 1/2: clases e identidades estables; seis cruces y seis entradas de una identidad por clase. Geometría excluyente y duplicados verificados para cada clase. No se interpreta como evaluación de precisión sobre video real.
- Vitest completo: 143 aprobadas en 62 archivos; tras endurecer el lookup de alias frente a propiedades heredadas, las dos pruebas del archivo nuevo pasan. Total distinto verificado: 144. Build TypeScript/Vite aprobado.
- Advertencias existentes: deprecación BlockingPortal y chunk Vite de 504.51KB minificado. Sin evaluación larga ni cambio en los pendientes humanos previos.

Reproducir desde raíz: `.\.venv\Scripts\python.exe -m pytest backend/tests/integration/test_model_vehicle_class_counting.py -o addopts='' -q`. Desde frontend: `npm test` y `npm run build`.
