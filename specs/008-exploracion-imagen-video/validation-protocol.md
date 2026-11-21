# Protocolo de validación y medición —008

**Estado**: protocolo previo a implementar. No contiene resultados de producto ni cierra aceptación. Se mantienen los umbrales de [spec.md](spec.md).

## 1. Congelación y material

Antes de modificar la presentación, registrar versiones, pesos/hashes/umbrales aprobados, dispositivo efectivo por etapa, encoder, dimensiones/FPS/duración, concurrencia y comandos de la línea base. La referencia legacy del renderer actual se congela en tests, no se añade un selector público para cambiar algoritmos.

Generar material autorizado/controlado:
- 10 escenas de imagen,3 densas, IDs largos/solapamientos/bordes/orientación canónica.
- >=6 clips con2 densos>=21actores, cruces/oclusión/cambio de escena, movimiento rápido y cero actores. Incluyen>=3 tramos continuos>=120cuadros para jitter.
- Manifiesto versionado con hashes de originales sintéticos, raw observaciones congeladas, trayectorias de referencia conocidas, segmentos/estratos y cuadros de revisión. La referencia no se deriva de la salida candidata.
- Separar material de ajuste del material reservado. Fijar alphas/reglas/reset y reserva antes de mirar resultados. Cambiar un parámetro exige nuevo profile_id/huella y reserva no usada para ajustar.

Las pruebas sintéticas acreditan geometría/lifecycle/recursos, no exactitud real del detector/OCR. No copiar placas privadas al repo.

## 2. Geometría, presentación y asociación

Imagen: Ajustar/100/200/400%,50 puntos/cajas por escena incluyendo límites/fracciones. Comparar DOM proyectado con transformación canónica, error<=1px CSS; no comparar con otra imagen orientada distinta. Verificar lista/selección/crops y ausencia de etiquetas. Al menos30 operaciones de zoom/pan por viewport con imagen cargada, reloj monotónico hasta render, p95 nearest-rank<=200ms.

Video: revisar al menos50 cuadros fijados por clip, todos los frames de segmentos de jitter y cuadros de corte/ausencia. Cero texto identificador en análisis, clases correctas, tamaños/FPS/duración y conteo completo. Comparar almacenado raw con baseline: identidad, clases, confidencias y cajas sin alteración por filtro. Conteo y evidencia se calculan sobre ese raw.

La referencia de tiempo es MP4 procesado CFR, i/fps. Comprobar salida con igual cantidad de cuadros escritos, dimensiones y FPS, duración dentro de1cuadro respecto baseline. No afirmar preservar PTS del original VFR.

## 3. Jitter y precisión temporal

Para cada cuadro válido con referencia r:
- residuo de centro e_c=(centro_presentado-centro_referencia)/diagonal_referencia.
- residuo de tamaño e_s=((ancho_presentado-ancho_ref)/ancho_ref,(alto_presentado-alto_ref)/alto_ref).
- J_center=RMS de norma de primeras diferencias de e_c; J_size igual para e_s. No usar velocidad real del vehículo como “jitter”.
- Medir ambos brazos con las mismas raw observaciones congeladas y cuadros; no excluir fallos, oclusiones difíciles o segmentos desfavorables después de mirar candidato.

Gate por cada segmento predefinido: canal con J_baseline>1e-6 exige J_candidate<=.8*J_baseline. Canal estable<=1e-6 permanece<=1e-6. La excepción de baseline ya estable se registra antes de ajustar, no elimina la obligación de comprobar precisión y ausencia de cajas inventadas.

IoU entre caja entera presentada y raw autorizada actual>=.90 en>=95% de cuadros válidos; también registrar todos los fallos y fallback raw. Una caja degenerada es fallo, no muestra descartable.

Medir lag de forma independiente: comparar trayectorias de referencia/presentación con desplazamientos enteros k=-3..3, sobre soporte común fijo; k óptimo minimiza error normalizado. Empates prefieren menor|k|. Exigir|k|<=1; trayectorias estacionarias se identifican explícitamente como no informativas para estimar lag. No declarar cero solo por compartir frame_index. Registrar cortes/huecos/clases/IDs y verificar que cada reinicio elimina estado viejo; jamás extrapolar ausencias.

gated-ema-v1 es la primera candidata, no un éxito demostrado. Si no supera gates, conservar representación segura y dejar SC-005 pendiente; no declarar entrega completa ni ajustar sobre reserva para fabricarlo.

## 4. Tiempo y memoria

Tres pares completos baseline/candidata por clip, orden AB/BA alternado, mismo hardware efectivo/modelos/umbrales/carga. Sin otros jobs ni tráfico que cambie entre brazos; mismo calentamiento declarado, primera llamada incluida o excluida igual y explícitamente.

Medir:
- tiempo monotónico desde primera decodificación hasta MP4 publicado, incluyendo dibujo, escritura y codificación.
- tiempos separados de inferencia/seguimiento, presentación y encoder; la suma no sustituye el end-to-end.
- RSS de proceso backend y del proceso FFmpeg propio, muestreado<=100ms; gate sobre el pico combinado, y desglose de ambos. No atribuirlo a asignación exclusiva de un job.
- RSS y límites del gateway por separado: debe arrancar sin modelos y transferir con buffers acotados; no descontar este coste de los informes.
- enriquecimiento por track/etapa y contadores de modelos aparte; no ocultarlo dentro de coste visual.

Por clip: mediana de tiempo y máximo pico combinado entre repeticiones<=110% baseline. Registrar todas las corridas/fallos, no seleccionar las mejores. No reducir FPS/resolución/cuadros/duración ni aumentar timeout/colas para pasar. UI y health de gateway/backend responden<=1s en los casos controlados. Medición de representación con raw congelado aísla el filtro; corrida completa con modelos aprobados acredita el coste real cuando se ejecuta.

## 5. Seguridad, idempotencia y lifecycle

Canario privado de test generado en entorno del gateway, nunca como literal de la app. Buscarlo en HTML/build/config/red de navegador/respuestas/logs públicos:0 apariciones. Verificar API directa aún requiere su clave, propietarios separados y no existe relay anónimo público.

Probar sesión/CSRF/Origin/Host, traversal/URL/query/redirect, streams acotados/cerrados, límites con cuerpo chunked, desconexión, Range200/206/416, TTL durante cuerpo y video pausado, reset y respuestas tardías.

Idempotencia: dos POST concurrentes, recibo perdido, replay tras completed/fallo, mismo key/diferente fingerprint, propietario distinto, cancelación/TTL y copia staged extra. Una sola fila/cola/inferencia por intención vigente. Ningún replay renueva expiración; nueva tentativa solo explícita cuando corresponde.

Fases: retrasar encoder/publicación con barreras;100% de cuadros no es etapa terminada. Cancelar/vencer dentro de FFmpeg y en finish, comprobar que no aparecen MP4/detecciones tardíos y que no se libera el cupo antes del proceso real.

## 6. Entrega y evidencias

Implementará scripts/evaluate_video_presentation.py y fixtures descritos en el plan. Resumen agregado propuesto: protocolo/profile/huellas, condiciones, conteos/segmentos, J_center/J_size por segmento, IoU/lag/fallback, tiempos/RSS por par y gate_pass con causas. No incluir imágenes privadas, OCR, rutas, cookies o claves.

validation.md/audit.md futuros deben distinguir pruebas sintéticas, benchmarks completos efectivamente ejecutados, pendientes y fallos. Capturas de todos los estados en tres viewports/texto200%. Revisión de propuesta de pausa/lista/ficha con dependencias reales; sin afirmar implementación de clicks temporales ni certificación WCAG completa. Pendientes006/007 y exactitud real siguen independientes.
