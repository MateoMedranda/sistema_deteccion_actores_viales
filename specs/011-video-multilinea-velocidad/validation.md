# Validación técnica011 —2026-11-25

Estado actual tras correcciones del 2026-11-26:84/85 tareas marcadas; T076–T085 corregidas. Los resultados del 2026-11-25 que siguen se conservan como antecedente. Pendiente externo: T071/SC-009, prueba de uso con cinco personas. Ver `human-validation.md`.

- Backend: suite completa556pruebas aprobadas; después se añadió un caso de fecha con zona y pasó el grupo contractual30/30.
- Frontend: suite completa191pruebas/72archivos aprobados; después pasó el grupo2/2 de cancelación aislada con un caso adicional.
- TypeScript/Vite: build aprobado. Permanece advertencia de chunk minificado>500kB; no bloquea el build. Backend conserva aviso de deprecación de anyio.
- Navegador Chromium:21combinaciones de escenario/tamaño verificadas en varias pasadas, más una medición de velocidad. Las tres pruebas finales de espera pasaron al consultar el prefijo real del backend; seis revalidaciones de layout/nombres60grafemas/latencia pasaron. La prueba temporal no se repitió en tablet/móvil.
- Reproducción de30s:0,5×=59,979s,1×=30,099s,2×=15,020s; dentro±5%. No son FPS de detección.
- Ensayo de rendimiento0/1/10líneas: objetivos de lock/GET/catch-up cumplidos. Ver informe y límites en `evidence/performance-review.md`. No se ejecutó comparación larga con modelos reales.

## Fallos encontrados y corregidos

Contrato pending/total, parser de objetos individuales, reconciliación al recargar bajo StrictMode, borrador inicial frente a configuración ya confirmada, mensaje al rechazar colores repetidos, visibilidad de espera sin ancla, espacio reservado en fullscreen y cancelación de un borrador sin descartar el de otra línea. La fecha de vencimiento exige zona horaria.

Los ensayos también corrigieron expectativas: uno de seis objetos cruza la prolongación, fuera del segmento; debe excluirse (5cruces). El prefijo del backend sigue avanzando mientras el canvas está pausado; su atributo solo cambia al repintar y no es un medidor vivo del backend.

## Operación y límites

Reiniciar API y gateway tras instalar `regex` con el Python3.12 existente. El frontend ofrece velocidades0,25×–2× y10líneas activas por defecto, nombres y colores únicos. Conteos exactos por tiempo fuente, identidad local y línea; no sumar tarjetas para obtener vehículos físicos únicos. Cambiar geometría reconstruye solo esa línea; metadata conserva eventos. El inventario global y la exportación siguen independientes.

Recarga: se conserva solo ID opaco y expiración en sessionStorage; backend autoriza y conserva configuración/cruces hasta el TTL original. Nuevo archivo, limpieza o reinicio de sesión descartan referencia y borradores. Una capacidad404 conserva el video; autenticación/vencimiento mantienen la autoridad existente. No se exponen claves al navegador.

Las pruebas usan servicios temporales9413/9414/9415 y no detienen procesos del usuario. La limpieza deliberada puede generar logs ApiError en el worker sintético al retirar un trabajo en marcha. Es un efecto del fixture, no un fallo de las verificaciones finales.


## Correcciones de convergencia T076–T085 —2026-11-26

Se corrigieron los diez hallazgos de Phase9 sin cambiar detección, seguimiento, modelos, configuración privada ni contratos HTTP. T071/SC-009 permanece sin marcar y no se ejecutó validación con personas ni comparación larga. La evidencia agregada actual está en [evidence/convergence-corrections.json](evidence/convergence-corrections.json); conserva también el resultado desfavorable inicial.

- Backend:562/562 aprobadas en la pasada final (88,23s), incluidas cinco regresiones nuevas de aislamiento por línea/revisión y padre vigente. La primera pasada tuvo561 aprobadas y un PermissionError de Windows al leer un perfil temporal; el archivo afectado pasó4/4 al repetirlo y después la suite completa pasó sin modificar el perfilador. Avisos: alias obsoleto de anyio y cinco incompatibilidades de record_property con el reporte JUnit xunit2.
- Frontend:221/221 aprobadas en73archivos (22,97s). TypeScript/Vite aprobados; continúa el aviso del chunk minificado mayor de500kB.
- Chromium:21/21 escenarios de conteo/recuperación/layout a1440/768/360px. Se conservaron los límites de búsqueda, diez ciclos de retroceso, veinte intentos futuros, pantalla completa y tacto/teclado. Los logs ApiError al retirar trabajos forman parte del teardown controlado.
- T084 usa ahora el reproductor, FrameCache, CountLineBar y consultas/proyección reales con decoder instrumentado: compara cajas, instante fuente, inspección de vehículo y cantidades a0,5×/1×/2×, conserva instancia/PTS/caché y verifica espera→reanudación/pausa explícita. El SourceDecoder real tiene pruebas de cola28frames, bloques8MiB y posters16MiB; FrameCache prueba rechazo atómico sobre16MiB y expulsión de ventanas antiguas. No se repitió la medición E2E temporal de30segundos; sus mediciones anteriores mantienen fecha y alcance originales. Estas pruebas no acreditan FPS de inferencia ni equivalencia de hardware edge.

El editor conserva una base confirmada y una propuesta independiente por UUID. Aplicar/eliminar una línea compone la colección desde el servidor más esa operación, sin confirmar otras propuestas; el cambio remoto se concilia y un conflicto exige decisión explícita. El dibujo sigue la geometría seleccionada, no puntos iniciales obsoletos. Limpiar un borrador comunica su estado vacío; los nombres/colores iniciales evitan tanto valores confirmados como otros borradores y el nombre confirmado se muestra normalizado.

El descriptor se recupera con espera creciente hasta8segundos entre intentos, sin solicitudes solapadas; mantiene la última configuración frente a fallos recuperables. Los cambios de video/sesión y401/403/410 cancelan solicitudes/reintentos. Importación y reconciliación verifican trabajo/generación/revisión; no se acepta una respuesta tardía ajena. La cuota acumulada, incluidas eliminadas, se comunica antes de rechazar nuevas altas y no impide editar/borrar las existentes.

El reducer ya no invalida todas las líneas cuando falla una. Aísla la línea fallida, conserva estados/eventos previos y permite avanzar a las demás; toda publicación de fallo comprueba generación, geometría, cursor y vigencia del padre. No se resucitan eliminadas ni se aplica un error al segmento que sustituyó al capturado.

Commits de producto de esta corrección: `45df949` (backend/T079) y `9273112` (frontend y regresiones T076–T078/T080–T085). Después del ajuste final de nombres/colores se repitió configuración de diez líneas:3/3aprobadas en1440/768/360px. Los21escenarios y estas3revalidaciones se registran por separado; no se suman como24casos distintos.
