# Quickstart de validación: Iteración 010

Guía para la futura implementación; las capacidades nuevas todavía no están implementadas. No ejecutar las pruebas previstas como si ya existieran. La revisión de esta fase solo comprueba documentos/contratos y deja evidencia en Git.

## Preparación

Trabajar en checkout principal y feature/010-video-detalle-conteo. Conservar cambios y .env privados. Usar Python3.12 compatible ya instalado y las dependencias fijadas; no cambiar pesos, GPU, intervalo ni hilos para atribuir resultados a esta iteración. No usar videos privados en fixtures/versionado.

Desde raíz, verificar rama y entorno sin cambiar de rama automáticamente:

~~~powershell
git branch --show-current
.\backend\start.ps1 -Service api -CheckEnvironment
~~~

API, gateway y frontend requieren terminales separadas. Detener solo instancias propias ya ejecutándose antes de duplicarlas; no matar procesos ajenos por puerto:

~~~powershell
# Terminal 1, desde raíz
.\backend\start.ps1 -Service api
# Terminal 2, desde raíz
.\backend\start.ps1 -Service gateway
# Terminal 3, desde raíz
npm --prefix frontend run dev
~~~

Si la terminal ya está dentro de frontend, usar `npm run dev` sin repetir --prefix frontend. Las URL/credenciales privadas existentes se mantienen; la UI sigue pasando por gateway.

## Escenarios de aceptación

1. **Ficha**: Abrir imagen y video sintéticos con todos los apartados. Comparar a360/768/1440. Recorrer la página hasta placa/cierre sin scroll sobre toda la ficha ni horizontal de página. Comprobar teclado/toque, foco y zoom local de placa.
2. **Temporalidad**: Fixture con la misma identidad en3s y20s, placa ausente al entrar y visible después. Pausar/seleccionar cada instante: el recorte/contexto deben ser distintos y exactos. Reabrir20s reutiliza el mismo inspection_id/asset_id. Nuevas revisiones de análisis durante30s no alternan imágenes ni reinician ampliación. Desordenar respuestas y cerrar/buscar no reabre ficha ni mezcla resultados.
3. **Extracción**: Probar VFR, PTS de origen no cero, rotación y frame predicho entre mediciones; comparar píxeles/timestamp con decoder autorizado. No debe ejecutarse detección de escena. Fuente no accesible, límites de extracción y crop inválido muestran indisponibilidad del contexto, sin sustituir por aparición antigua.
4. **Conteo**: Antes de subir, primer frame local con editor y flecha. Escena determinista: dos cruces válidos, uno inverso, contacto/retorno, cruce de prolongación y predicción desmentida. Solo los dos válidos suman. Inverso seguido por cruce válido de la misma identidad suma una vez al cruce correcto; simultáneos suman su cantidad. Invertir sentido en borrador no cambia acumulado hasta aplicar.
5. **Historia/revisiones**: Dos recorridos y cinco saltos antes/después de eventos; total correcto por posición. Repetir PUT con revisión vigente/config idéntica no reinicia; revisión obsoleta409. Tras pérdida de respuesta, GET y conciliación evitan sobrescribir otra configuración. Reducer pendiente indica cobertura, no muestra eventos futuros ni un Track ID como cantidad. Caso de borde: reducer cubre hasta1.000.000us exclusivo y el siguiente cuadro publicado inicia allí con un cruce; consultar exactamente1.000.000us permanece pending hasta reducir ese cuadro, nunca ready con el valor anterior.
6. **Inventario**: Una identidad en100 cuadros cuenta una vez; varias clases y empates se resuelven según [data-model.md](data-model.md). Personas excluidas y clases sin catalogar visibles. Repetir publicación/reiniciar no duplica votos. Conteo activado/desactivado y enriquecimiento no alteran total final. Cero produce cero; fallo/cancelación produce parcial con cobertura.
7. **Descarga**: Exportar variante vehicle-labels-v1 tras análisis completo. Comprobar cada caja/ID/clase y acentos, colores, bordes y densidad en cuadros del MP4 decodificado, dimensiones/duración/velocidad conservadas conforme al exportador actual. Marcar detector/OCR para fallar si se invocan: exportación debe seguir funcionando. Tener un MP4 boxes-v1 previo no satisface la variante etiquetada.
8. **Ciclo de vida**: Otro propietario404, sesión inválida401/403, CSRF rechazado, generación/revisión obsoletas409 y TTL410. Retirar/vencer durante extracción, modelo, backfill y encoding impide publicación y limpia tablas/temporales al liberar leases. Un404 local de inspección no retira un video válido. Saturación de cola/cuota produce429 acotado, sin bucle de creación. Vencer solo la inspección y repetir POST de la misma clave debe dar410 local sin extender TTL ni ejecutar OCR; padre todavía reproducible. Simular native decode bloqueado acredita watchdog/terminate/join y ausencia de hijos/temporales huérfanos.
9. **Compatibilidad**: Rutas /summary, /playback/count, /tracks/{id}/enrich y exportación sin renderer conservan contratos. Backfill antiguo no usa predicciones como mediciones; si procedencia insuficiente, unavailable/reanalysis_required. Fuente/observaciones compatibles permiten capacidades sin un nuevo detector.

Consultar [contracts/README.md](contracts/README.md) para cuerpos, estados y errores; [contracts/ui.md](contracts/ui.md) para interacción. Las pruebas automatizadas nuevas deben usar archivos temporales/puertos aislados y no el trabajo/runtime del usuario.

## Comandos de verificación tras implementar

~~~powershell
# Desde raíz; entorno existente compatible
.\.venv\Scripts\python.exe -m pytest backend/tests
npm --prefix frontend test
npm --prefix frontend run build
~~~

Playwright010 se añadirá en tasks/implement con config/servidores de prueba aislados, siguiendo los e2e009 existentes. El comando previsto, una vez creado el archivo, será:

~~~powershell
npm --prefix frontend run test:e2e -- --config=playwright.010.config.ts
~~~

La suite de navegador debe incluir al menos una imagen y un video controlados y revisión visual de sus capturas/MP4. No presentar pruebas de modelo falso como medidas de precisión real.

## Rendimiento y documentos

Comparar base y cambio sobre el mismo tramo corto, misma configuración y carga comparable, sin seleccionar/exportar: tres pares acotados, entorno registrado, medianas y variación; investigar >5 % de regresión del análisis. Este experimento nuevo no sustituye ni reactiva la comparación larga previamente diferida.

Al probar con un análisis ordinario nuevo, conservar el informe operativo:

~~~powershell
.\.venv\Scripts\python.exe .\backend\scripts\report_video_profile.py --latest
~~~

El --latest debe seguir refiriéndose al análisis, nunca a inspecciones/exportaciones. Registrar latencia de extracción/cola/enriquecimiento y límites en perfiles separados sin medios ni lecturas OCR. Conservar cobertura de inventario/conteo y solicitudes nuevas frente a reutilizadas. Resultados futuros en validation.md/evidence/ de010, enlazados desde docs/registro-evolucion-sistema.md; no versionar .env, videos, placas ni recortes. Mantener explícitos los gates largos/humanos de009 pendientes.

## Referencia previa de publicación y elegibilidad de conteo

Al ejecutar T001, antes de cambiar código de producto, crear el harness autocontenido y capturar publication-baseline.json con calentamiento+al menos3 mediciones, fixture/parámetros, entorno y huella fuente. No depende de T002 ni crea trabajo privado. El harness debe ofrecer captura explícita de solo primera escritura y comparación que nunca sobrescriba esa referencia. T071 reutiliza el mismo caso y guarda candidato/comparación aparte; si falta base o no es comparable, queda pendiente/fallida y no se declara aceleración. No ejecutar esta prueba ahora: corresponde a implementar T001/T071.

El caso de conteo debe incluir persona y clase desconocida que cruzan sin sumar, bicicleta/moto elegibles, y clase que cambia tras un evento confirmado sin modificar el histórico. Los votos posteriores del inventario y OCR no deciden elegibilidad retrospectiva. El resumen conserva categorías desconocidas para revisión aunque el contador no las admita.
