# Validación efectiva — 009

Fecha:2026-11-22. Rama feature/009-video-progresivo, checkout principal. **Entrega funcional; aceptación exhaustiva pendiente.** El usuario indicó cerrar con pruebas funcionales/commit y diferir la comparación larga. Se detuvieron solo los procesos propios del benchmark; no se detuvo su servicio.

## Resultado automático

- Backend:320 pruebas aprobadas, incluidas regresiones de imágenes, video final y conteo.
- Frontend:118 pruebas aprobadas; compilación TypeScript/Vite aprobada.
- Navegadores:20 escenarios aprobados en la matriz Chromium1440/768/360, Firefox y WebKit Windows. WebKit acredita salida segura por incompatibilidad, no reproducción. Rechequeo final de navegación/toque/fullscreen documentado al cerrar.
- Corpus sintético40s,640x360,30fps: primer tramo observado entre520,83 y1.329,15ms después del commit de5s;30/30 saltos<1s por configuración compatible;150 cuadros únicos en cada ventana disponible de5s. Detalles: evidence/browser-metrics.json.
- Video real autorizado:3.611 cuadros comparados con OpenCV, cero diferencias de píxeles y sin cuadros extra. evidence/pixel-parity.json. No se incorporaron medios, placas, secretos ni rutas privadas a Git.

## Cobertura y límites de la evidencia

| Criterio | Evidencia/estado |
|---|---|
| SC001 | PASS controlado, cuatro configuraciones compatibles y clip>=30s; no sustituye primera reproducción con modelos reales |
| SC002 | Clamp, Home/End, navegación y salida visible confirmada; fuentes/medios owner-scoped; ampliar matriz120s/42s y dispositivos reales |
| SC003 |30/30 saltos ordinarios<1s; pendiente medición con historial expulsado del caché |
| SC004 | Diez identidades en lista/fichas y pruebas de asociación a recortes, revisiones y selección; pendiente latencia commit→ficha con corpus real |
| SC005 | PTS CFR/VFR/B-frames/offset/rotación en decoder; identidad inmutable y píxeles en navegador; ampliar todos los formatos y condiciones reales |
| SC006 |150/150 cuadros en ventanas controladas de5s a1x; pendiente serie prolongada con esperas separadas y modelos reales |
| SC007 | Pendiente: tres pares reales completos sobre candidato final |
| SC008 | Publicación atómica/rollback, retiro concurrente, propiedad, cursor, stream, recuperación y respuestas tardías probados |
| SC009 | Pendiente cinco participantes reales; no se simula cumplimiento |
| SC010 | Cachés acotados y cierre de recursos probados; pendiente RSS API+workers+encoder+gateway activo y reproductor |

Las pruebas se consolidaron en menos archivos que los previstos. Véase audit.md para la correspondencia. Un PASS de pruebas automáticas no cierra todos los criterios de aceptación.

## Hallazgos corregidos durante implementación

1. HTMLVideoElement/requestVideoFrameCallback no mantuvo identidad de píxeles bajo carga. Se reemplazó por VideoDecoder/VideoFrame inmutable, con mp4box2.6.0, CTS/index/PTS contrastados y sin fallback de original visible.
2. La conversión predeterminada de PyAV para BT.709 no reproducía los píxeles del pipeline OpenCV. Se conserva ahora su perfil ITU601/BICUBIC; la comparación completa dio cero diferencias.
3. Se corrigieron lectura concurrente SQLite, cierre de recursos, asociaciones de atributos, limpieza durante streams y vencimiento oculto.
4. Ranking top-K ligero, sightings por lote y publicación de resultados solo al cambiar evitan consultas/serializaciones repetidas. No cambian pesos, umbrales, muestreo ni política final.

Un ensayo diagnóstico anterior a estas correcciones finalizó3.611 cuadros en ambos brazos: análisis570,813s frente696,016s y ratio1,2193, fuera del gate1,10; observaciones52.055 frente52.082, también incompatibles. Ese candidato fue descartado. No se usan esos números como aceptación del código corregido.

La nueva comparación quedó interrumpida por indicación del usuario durante su primer brazo baseline. No hay tres pares finales válidos ni se afirma que la versión actual cumpla los ratios1,10/1,20. El arnés actual mide backend/OCR/encoder; completar alcance de gateway activo/reproductor según validation-plan.md. Los registros detallados permanecen privados en .runtime.

## Reproducibilidad y seguridad

Los tests usan bases/archivos temporales y puertos9413/9414/9415. La preparación automática genera únicamente clips sintéticos; selecciona un Python3.12 con dependencias. API key y URL de backend privados siguen en backend/.env y backend/.env.web, sin modificaciones. Se conservaron los CSV de métricas previos y la rama solicitada.

GET no inicia modelos; navegar/seleccionar tampoco. La creación sin presentation conserva modo legacy; idempotencia separa modos. El fallo técnico conserva prefijo autorizado hasta su TTL, mientras DELETE/limpieza/vencimiento lo retiran. La recuperación no reinfiere una generación interrumpida.

Compatibilidad de vista progresiva: AVC/WebCodecs, MP4 no fragmentado, una edición normal y orientación ortogonal. Los demás casos informan incompatibilidad y conservan datos consultables. No se acredita calidad OCR real con fixtures ni usabilidad humana con screenshots.


## Entrega de inspección selectiva y conteo opcional — 2026-11-22

Cambio aprobado por el usuario: detección/seguimiento sin enriquecimiento automático en el frontend nuevo, consulta por selección y conteo opcional. Se conservaron imágenes, exportación final, modo automático de clientes anteriores y conteo legacy. No se ejecutó la comparación larga ni modelos reales de rendimiento en esta entrega.

- Backend: **331 pruebas aprobadas** en suite completa. Nuevos casos: cero evaluaciones antes de seleccionar, solo el Track ID solicitado, primera evidencia raw disponible antes de OCR, repetición sin evaluación adicional, propiedad/retiro, línea idempotente, cambio de línea, consulta histórica0→1→0 sin duplicados, rutas y parámetros, métricas por cuadro y memoria, y selector de Python compatible sin iniciar servicios.
- Frontend: **124 pruebas aprobadas** (suite actual), incluida recuperación con revisión de enriquecimiento constante, identidad de diez fichas, estados distintos de fallido/parcial/no aplicable y recuperación de una configuración de conteo aceptada cuya respuesta se perdió, sin repetir PUT.
- Compilación TypeScript/Vite aprobada. No se cambiaron dependencias, modelos, pesos, muestreo ni .env.
- Navegadores: matriz de **25 escenarios aprobados** (Chromium escritorio/tablet/móvil, Firefox y WebKit Windows) y **4 regresiones adicionales aprobadas** de fin natural/reproducción explícita y fallo transitorio de fuente en escritorio/móvil. WebKit Windows solo acredita salida segura cuando falta WebCodecs; no se presenta como reproducción/conteo soportados.
- En los cuatro entornos con WebCodecs del caso nuevo, atributos/OCR tuvieron cero llamadas antes de seleccionar, la consulta elegida usó hastaK evidencias y repetirla no añadió evaluaciones. Con una sola subida, dibujo por puntero/toque y ajustes de teclado, el contador mostró **0→5→0→5** al navegar Home/End/Home/End, y Desactivar retiró el contador. Texto200% sin overflow de página. Los recortes y placas de estas pruebas son sintéticos.
- Se inspeccionó la captura del flujo de escritorio: ficha lateral sin lista encima, recortes con sus etiquetas, línea sobre la escena, contador superior derecho y editor inferior. Se corrigió la superposición de la ficha con controles inferiores; también se aisló la pausa de las pruebas fuera del recurso del modelo y se retiraron trabajos sintéticos entre escenarios.

La consulta bajo demanda fija hastaK recortes disponibles al primer clic; se reutiliza mientras dure la autorización del trabajo y no se refina automáticamente con evidencia futura. Pausar detiene el reproductor, no la detección del backend. El conteo usa las reglas existentes de lado/dirección y un cruce por Track ID; la geometría representa la línea de conteo según esas reglas.

**Límites pendientes**: no se acredita un nuevo FPS real ni el gate de coste/memoria de la política automática original; cambiar política exige reportar condiciones comparables. T039/T074–T077 y las tareas de convergencia T085–T088/T090–T091 siguen abiertas. No se simula prueba humana ni se relajan umbrales. T081–T084/T089/T092 cuentan con corrección/regresión relacionada en esta entrega.

**Arranque**: reiniciar API y gateway para cargar el parámetro y las rutas nuevas, y recargar la página para renovar sesión. Un proceso antiguo sin reload puede seguir devolviendo422 durante la subida. Los comandos están en quickstart.md; `start.ps1 -CheckEnvironment` no inicia servicios.


## Corrección de regresiones reportadas: identidad y editor — 2026-11-22

Causa confirmada del recorte incorrecto: model.track registraba callbacks con persist=False; el código instalado captura ese valor y recreaba ByteTrack en cada predicción. El mismo ID local se reasignaba según detecciones de cada cuadro, mezclando evidencia de Car/Truck/Van. No era una consulta aleatoria de la ficha: la clave Track ID ya estaba corrupta antes de seleccionar.

Corrección: tracker BYTETracker propio por video, predicción raw del mismo modelo/umbral/dispositivo y configuración bytetrack.yaml anterior. Imágenes intercaladas no mutan seguimiento de video. Regresiones invierten orden de detecciones, intercalan predicción de imágenes y reinician un trabajo sin recargar pesos.

Diagnóstico real acotado:40cuadros del mismo video autorizado, sin OCR ni benchmark largo. Antes, Track ID10 alternó Car→Big Truck→Car→Van→Car→Big Truck→Van→Car; corregido, Track ID10 permaneció Car. Persisten fluctuaciones de clase entre Truck/Big Truck en otros tracks; no se afirma identidad perfecta ni aceptación del video completo. No se guardaron medios/lecturas privadas en Git. Agregados en evidence/tracker-identity-fix.json.

Editor restaurado: primer cuadro confirmado automático (preview acotada a1280px, mismo decoder/orientación), dibujo arrastrando, extremos con captura de puntero y teclado, traslación de toda la línea acotada a la imagen. Las coordenadas y otro fotograma son secundarios, plegados. Borrar retira también conteo activo. No se repite detección al editar.

Pruebas efectivas:333 backend,125 frontend y compilación aprobados; caso E2E de inspección/conteo aprobado en escritorio/tablet/móvil, con primer fotograma automático; verificación adicional de arrastre completo con12movimientos reales y desplazamiento esperado de ambos extremos en escritorio. La prueba unitaria verifica creación, traslación, extremo, teclado y borrado. No se ejecutó comparación larga ni prueba humana.

Despliegue local: reiniciar la API para crear modelos/trackers limpios y analizar el video otra vez. Un trabajo anterior ya tiene IDs/evidencias mezclados; no se corrige al recargar la página ni se reescribe automáticamente. Los gates de rendimiento/usabilidad previos continúan pendientes.


## Regresión de publicación en el borde — 2026-11-22

El reporte de0/3611cuadros fue reproducido con la publicación real del primer lote. En el cuadro11 el tracker de Kalman produjo una caja con x_max1934 para una imagen de1920px; las siguientes llegaron a1951/1966. El store rechazó invalid_observation y revirtió el lote completo de15cuadros, dejando el límite publicado en cero. La prueba previa de40cuadros comprobaba IDs, pero no enviaba esas coordenadas a la publicación transaccional.

El adaptador ahora recorta las coordenadas exportadas al ancho/alto de cada cuadro, como hacía Results.update en el flujo anterior, y omite cajas degeneradas completamente fuera de la imagen. No altera el estado interno de ByteTrack, modelo, umbral ni validación del store. El pipeline registra excepción/tipo/código seguro para diagnosticar futuros errores sin publicar texto libre, rutas o placas.

Regresiones: test_tracker_identity incluye salida por borde derecho, borde superior y caja completamente externa; test_progressive_operational_metrics verifica diagnóstico seguro ante rechazo de publicación. Suite backend completa:335aprobadas. Verificación real aislada:60cuadros,4lotes publicados y2.000.000us disponibles; validación activa y sin comparación larga. No se modificaron datos del servicio activo ni se ejecutó OCR masivo.

Reiniciar API y crear un análisis nuevo tras limpiar la selección anterior; el trabajo fallido no se reanuda automáticamente. La solución conserva seguimiento persistente y el editor arrastrable del primer fotograma.


## Instrumentación por etapas — 2026-11-24

- Cambio solicitado: T107–T109, medición del flujo existente antes de decidir optimizaciones. No se cambian modelos, píxeles, umbrales, frecuencia, política de evidencias, identidad, conteo ni exportación.
- Verificación: 13 pruebas focalizadas aprobadas; suite completa backend: **343 passed** (una advertencia de deprecación Starlette/AnyIO). Tras la revisión final del cierre del decodificador y dos casos adicionales de atribución exacta YOLO/ByteTrack y fallo de exportación: **19 regresiones pertinentes aprobadas**. Sin cambios frontend ni nuevas dependencias.
- Contabilidad con reloj controlado: espera, detección, tracking, otros tiempos y conversión final no se mezclan; costes por cuadro y porcentaje se calculan con base explícita. El tiempo de un bloque que falla también queda contabilizado.
- Igualdad del tracker normal/perfilado en ocho cuadros sintéticos con orden de detecciones alternado; se conserva salida de detecciones/IDs. El camino real llama una vez a predict por cuadro, como antes.
- Integración: video sintético de doce cuadros completa análisis/exportación con informe, separación de etapas y lectura CLI por último/ID/JSON; fallo de detección previo al primer lote genera informe seguro sin texto privado; carpeta de informe no escribible no falla el video.
- Resúmenes periódicos reemplazan un único archivo por trabajo, con estructura de agregados de memoria constante. No almacenan píxeles, matrículas, propietario, credenciales ni la ruta/nombre de la carga.
- No se ejecutó un video privado ni comparación larga. No hay todavía datos reales de esta instrumentación para identificar el cuello de botella del equipo del usuario. La guía de obtención está en quickstart.md. T039/T074–T077 y los pendientes de convergencia no se cierran por esta entrega.


## Intervalo de detección configurable — 2026-11-24

- T110–T112 implementan el cambio aprobado por el usuario, manteniendo el modo 1. No se cambian modelos, umbral ni píxeles de entrada; se cambia únicamente la frecuencia observada y la predicción de estado entre observaciones, con evidencia y conteo protegidos frente a estimaciones.
- Las 12 regresiones iniciales fallaron por ausencia del comportamiento esperado antes de implementarlo. Pruebas focalizadas posteriores: 22 aprobadas; la suite completa incorpora además recuperación del mismo Track ID tras una oclusión breve: **359 pruebas backend aprobadas** (una advertencia de deprecación Starlette/AnyIO).
- Video sintético de 12 cuadros: intervalos 1 y 2 conservan doce cuadros/PTS, dos IDs estables y el mismo cruce confirmado; el modo 2 hace seis llamadas YOLO, publica seis cuadros predichos y guarda evidencia/filas legacy solo de observaciones reales. Un cruce predicho que se corrige sin cruzar no suma; un cruce real posterior suma una vez y retroceder no duplica.
- Configuración inválida se rechaza; reset reinicia cronología e identidades de trabajo; perder una medición programada no marca tracks como perdidos, y tracks realmente perdidos no se dibujan como predicciones. Un adaptador incompatible vuelve a intervalo efectivo 1 y lo declara en el perfil.
- Diagnóstico acotado con modelo/video real autorizado: primeros 60 cuadros, misma cronología confirmada y 60/30 llamadas YOLO para intervalos 1/2. Cruces en la línea de prueba y=.7: 3/3; igualdad: True. Contexto y hashes en evidence/detection-interval-check.json. No ejecuta OCR, exportación completa ni benchmark largo; no acredita calidad exhaustiva ni una cifra de FPS del pipeline completo. Los tracks únicos del tramo fueron 24/19 y las observaciones 742/726: no se declara igualdad exhaustiva de detecciones ni se atribuye esa diferencia a mejora o pérdida sin evaluación de identidad contra evidencia visual.
- Los pendientes anteriores de evaluación larga/humana permanecen abiertos. Repetir un análisis ordinario tras reiniciar la API permite comparar el perfil con el del usuario.

Verificación complementaria de compatibilidad: **125 pruebas frontend aprobadas** y compilación TypeScript/Vite correcta. Configuración local: únicamente VIDEO_DETECTION_INTERVAL=2, conservando los demás bytes del .env; variable privada excluida de Git.
