# Evaluación de placas — 007

Protocolo futuro de validación. Ninguna cifra de mejora se ha medido en esta fase. Se separan presentación visual, lógica sintética y exactitud con modelos/medios reales; una captura o fixture no acredita SC-006.

## 1. Línea base inmutable

baseline-v1 es la lectura vigente de enrichment_processing.py y plate_quality.py: lectura del crop original; si falta o confidence < retry_threshold, rectify_plate y conservative_enhance, luego segundo OCR; reemplazo solo con mayor confianza; read solo con texto y confidence >= accept_threshold. Mantener igualdad exacta en los umbrales límite.

conservative_enhance actual: scale=max(1,min(4,64/height)), dimensiones round(width*scale), round(height*scale), INTER_CUBIC, gris, CLAHE(2.0,8x8), borde replicado8 y retorno BGR. rectify_plate actual estima ángulo por Canny/minAreaRect y rota solo si 0.5<=abs(angle)<=15, ampliando canvas. Congelar parámetros/outputs y decisiones de política en pruebas antes de refactor. No añadir denoise o cambiar redondeos a esta base.

used_enhancement=True indica que se intentó reintento, aunque no gane. Nuevas imágenes registran provenance exacta; no inferir retrospectivamente selected_variant. Video sigue baseline vigente.

## 2. Perfiles candidatos iniciales

Son recetas deterministas a evaluar, no algoritmos aprobados ni lectura desplegada:

| Perfil | Receta |
|---|---|
| bilateral-clahe-v1 | crop original -> gray -> bilateral(d=5,sigmaColor=25,sigmaSpace=3) -> ampliación entera1..4 buscando alto64, INTER_CUBIC -> CLAHE(2.0,8x8) -> padding replicado8 -> BGR |
| bilateral-adaptive-v1 | crop original -> gray -> mismo bilateral y ampliación -> adaptive Gaussian THRESH_BINARY, blockSize11,C=2 -> padding8 -> BGR |

No deskew nuevo, perspectiva, reconstrucción, realce de bordes agresivo ni modificaciones de modelos/umbrales. Limitar lado<=2048, salida con padding<=2Mpx; elegir escala entera menor que cumpla. Si escala1 no cabe, lado<2, intensidad uniforme o la dimensión no admite block11, esa variante es no aplicable. No alterar silenciosamente su receta para que quepa. El perfil visual display-contrast-v1 es distinto: sin bilateral, umbral, deskew o padding; ver plan/data-model.

candidate-rescue-v1:
1. Ejecutar baseline-v1. Si read, devolver su lectura intacta, sin candidatas. Si failed/not_detected o sin localización fiable, conservar estado.
2. Solo si unreadable con crop válido, intentar las dos variantes aplicables desde el MISMO original, nunca una sobre la otra. Respetar los semáforos existentes de inferencia y un presupuesto adicional de 10 s por placa para el rescate; comprobar TTL/cancelación entre llamadas. Si el presupuesto se agota antes de completar las candidatas aplicables, no seleccionar un resultado parcial del rescate: conservar baseline y registrar corte seguro. Una llamada de modelo iniciada puede terminar sin publicar.
3. Aceptable = texto no vacío y confianza real >= accept_threshold vigente. Si ninguna aceptable, conservar estado baseline; si las aceptables discrepan tras normalización fija, unreadable y text=null. Si hay una, o coinciden todas, usar la observación de mayor confianza; empate: orden anterior. No sumar scores ni fabricar consenso/certeza.
4. attempted_variants refleja solo intentos reales; used_enhancement=true si se intentó cualquier variante procesada, aun si no se ejecutó legacy-retry; selected_variant solo el origen del texto read. No guardar textos de las descartadas. Ni selector visual ni hover invocan esta política.
5. El despliegue conserva baseline-v1. Promoción de candidate-rescue-v1 requiere reporte que supere todos los puntos del gate y cambio explícito de composición/configuración. No crear endpoint/UI para saltárselo. Si no hay evidencia suficiente, US4 queda pendiente.

Estos son parámetros iniciales cerrados para implementar el evaluador. Se podrán ajustar únicamente en el conjunto de ajuste; todo cambio crea versión/hash de perfil nuevo y se congela antes de evaluar la reserva. No cambiar detectores, pesos, clases o thresholds para mejorar el resultado del candidato.

## 3. Conjuntos y referencias

- Conjunto de ajuste independiente, recomendado >=30 placas; separado por escena/vehículo de la reserva. Ninguna variante o decisión se ajusta mirando resultados de reserva.
- Reserva >=60 placas con referencia verificada: >=30 degradadas y >=30 control. Registrar grupo/estrato antes de correr; incluir bajo contraste, ruido, tamaño reducido e inclinación, evitando que todas las difíciles sean del mismo caso.
- Manifiesto privado fuera del repo: scene_id/group_id pseudónimos, rutas privadas autorizadas de originales, geometría/identidad de referencia y texto verificado por revisión independiente. Declarar qué fuentes se usaron para verificar la referencia; no inventarla desde la misma lectura que se evalúa.
- Fijar asociación de cada placa al resultado de detección/localización sobre la misma imagen canónica antes de comparar OCR, sin elegir por parecido de texto. Duplicados/asociaciones ambiguas se resuelven y congelan antes de abrir resultados.
- Ejecutar detector/localizador aprobados sin cambiar sus parámetros; los dos brazos reciben los mismos crops realmente producidos. No sustituir fallos de localización por crops de referencia perfectos ni omitir muestras difíciles: sin evidencia, predicción vacía y fallo contado. El preprocesamiento canónico de 006 es igual en ambos.
- Datos de reserva observados durante ajuste dejan de ser reserva y deben reemplazarse por un nuevo conjunto independiente. Si la base ya es perfecta y no puede superar +5pp, registrar gate no superado, sin seleccionar un subconjunto favorable después.
- Fixtures sintéticos sirven para asociación, geometría, privacidad y carreras; su resultado no se mezcla con la exactitud real.

## 4. Métricas predefinidas

Normalización de comparación: Unicode NFKC, mayúsculas y eliminación de espacios y guion ASCII de separación; no sustituir O/0, I/1 ni otros símbolos ambiguos. Aplicar lo mismo a referencia/predicción, publicar la regla antes de evaluar y mantenerla idéntica. La regla es del evaluador, no un cambio al texto servido en producción.

Por brazo:
- Coincidencia completa = placas con predicción publicada igual a referencia / TOTAL de placas del grupo. Unreadable, failed o sin localización cuentan como no coincidencia.
- CER = suma de distancias Levenshtein (sustituciones+inserciones+eliminaciones) / suma de caracteres de referencia. Predicción no aceptada = cadena vacía.
- Lectura equivocada aceptada = status read con texto normalizado distinto de referencia; informar conteo y tasa con denominador explícito.
- Cobertura read y estados por estrato, intentos OCR/placa y variantes seleccionadas, sin texto en el informe compartido.
- Duración por etapa/placa y total de OCR (incluida la base y rescates), p50/p95/máximo, RSS inicial/final/máximo muestreado. Separar tiempos de detección/localización compartidas, lectura y visualización; no declarar como latencia end-to-end una suma estimada sin medirla.

Registrar hardware/CPU/GPU/RAM, versiones, hashes de pesos y perfiles, thresholds explícitos no sensibles, concurrencia y orden de ejecución. Alternar orden de brazos por grupo, mismo calentamiento documentado y condiciones; conservar resultados emparejados privados para auditoría. RSS es del proceso, no asignación exclusiva por placa.

## 5. Gate SC-006

Todos son obligatorios sobre la reserva congelada:
1. Ganancia >=5 puntos porcentuales de coincidencia completa en degradadas.
2. Coincidencia completa global no inferior a baseline-v1.
3. Número de lecturas equivocadas aceptadas no superior.
4. CER global no superior.

El evaluador calcula gate_pass a partir de conteos/denominadores y rechaza reserva insuficiente, IDs repetidos, fuga entre splits o referencias ausentes. Una confianza mayor o una demostración visual no reemplaza ningún punto. La promoción de una receta distinta requiere repetir el proceso con reserva válida; sin promoción, el reporte deja visible el objetivo pendiente.

## 6. Validación visual y rendimiento

Usar >=30 placas válidas independientes de la medición de exactitud (pueden pertenecer a la misma reserva una vez congelada sin ajustar perfiles). Medir de activación a PNG correcto decodificado/renderizado: 30 solicitudes frías, vaciar caché entre muestras, y serie caliente separada. p95 por rango más cercano ceil(0.95*N); para N=30 corresponde a muestra ordenada29. Requiere derivada disponible en las30 para afirmar este objetivo; fallos no se cuentan como éxito rápido. Objetivo p95<=2s y ningún intento local >10s.

Cuerpos/decode suspendidos, errores, carreras y TTL se prueban aparte con reloj/barreras. Las30 comparaciones conservan identidad/ROI/original y metadata; medir purga<=2s sin tráfico y memoria acotada tras ciclos/expulsión. Revisar apariencia original/procesada sin afirmar que sea información recuperada.

## 7. Salidas y aceptación

El futuro scripts/evaluate_plate_profiles.py generará evaluation-summary.json solo agregado: versión de protocolo, huellas de manifiesto/perfiles/modelos, conteos/grupos, métricas/costes, condiciones y gate_pass/causa. Nada de rutas privadas, imágenes, texto, credenciales o resultados por matrícula. Artefactos detallados privados tienen retención definida por el dueño, no se añaden al historial del producto.

Sin medios/referencias: registrar NOT_RUN y dependencia, nunca PASS. Si no supera gate: candidato no promovido y US4/SC-006/SC-009 de mayor exactitud siguen pendientes; se puede validar por separado US1/2/3 y el evaluador. Esto no cierra T067/T068 históricos de 006.
