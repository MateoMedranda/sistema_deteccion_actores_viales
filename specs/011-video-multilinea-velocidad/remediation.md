# Corrección autorizada y comprobación documental de011 —2026-11-25

Rama feature/011-video-multilinea-velocidad, checkout principal. El usuario autorizó proponer y aplicar las correcciones después de analyze. Solo se modifican documentación, descripciones de tareas y sus puntos recalculados; no código ni configuración privada.

## I1 — regla temporal consistente

Se distinguen dos verificaciones: la respuesta corresponde al at_us solicitado por esa petición; su cantidad ready puede seguir mostrándose en cuadros posteriores solo dentro de [snapshot.at_us,line.valid_until_us), con el mismo contexto. Fuera del intervalo se actualiza solo esa tarjeta. Un seek nuevo o cambio de generación/revisión descarta respuestas en vuelo anteriores. Se armonizan data-model§8/§10 y contracts/README; se conserva la exactitud, no se exige una consulta por cuadro y no cambian DTOs ni endpoints.

## U1 — gate de fundamentos acotado

T011 solo verifica creación/reapertura aditiva, claves/índice y purge de filas de fixtures sin invocar el servicio ni rutas posteriores. T014 cierra lo disponible al terminar fundamentos. El descriptor funcional vacío queda en T015 y las cuotas/tombstones/admitted_count en T016, pruebas de US1 satisfechas por T019–T022. No se añaden tareas ni se cambian dependencias o prioridades.

## Comprobación reproducida

75 tareas pendientes,144dependencias acíclicas y23marcas de paralelismo. Cobertura26/26FR y10/10SC; todos los paths y etiquetas de fase válidos. Comparación con4af9ee0 confirma mismos IDs/aristas/paralelismo/story. Script oficial de PTS recalculado:365de plan, sin añadidos/eliminados y75filas revisadas por agente, sin heurísticas. Descripciones del CSV coinciden con tasks.md.

JSON Schema:11definiciones válidas;9ejemplos positivos aceptados y12negativos estructurales rechazados. Los10casos semánticos siguen siendo pruebas futuras de producto, no se presentan como aprobación funcional. No se ejecutaron modelos, suite de producto, validaciones humanas ni comparación larga.

Comprobación de I1/U1: ambos corregidos, sin hallazgos conocidos pendientes ni violaciones constitucionales detectadas. El reanálisis final vuelve a leer los artefactos confirmados en modo de solo lectura. La entrega queda documentalmente preparada para implementar, no implementada; T071 y los gates humanos/largos conservan su condición futura.
