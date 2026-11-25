# Validación del diseño — Iteración 010

Fecha: 2026-11-24. Etapa: speckit-plan. Resultado: listo para generar tareas; funcionalidades aún no implementadas.

## Entrada y alcance verificados

- Checkout principal, rama feature/010-video-detalle-conteo conservada; base de esta etapa 1c0f4e5.
- spec.md y checklist de especificación se mantienen sin modificaciones. Se conservan archivos previos, incluidos CSV no versionados de otras sesiones.
- Plantilla de plan resuelta por setup-plan.ps1 y ruta explícita specs/010-video-detalle-conteo; la salida del script normaliza el nombre de feature, mientras Git mantiene el prefijo feature/.
- Hook before_plan de métricas ejecutado con modelo/nivel declarados previamente por el usuario. YAML válido y sin hooks after_plan registrados.

## Revisión de investigación y diseño

Tres investigaciones de solo lectura revisaron código actual: inspección/evidencia, conteo/inventario y UI/exportación. La consolidación resolvió las causas verificadas de scroll, caché por identidad sin tiempo, evidencia primaria cambiante, conteo de recta infinita, resumen por filas y exportación sin etiquetas.

Una segunda revisión detectó y corrigió durante la redacción:

1. Metadata de placa de imagen incompatible con inspecciones: DTO/parser de video específicos, misma cabecera versionada y transformación visual compartida, sin IDs fabricados.
2. Posible renovación indebida de TTL tras borrar un contexto: expiry fijo y tombstone mínimo hasta TTL padre, contando para cuota de admisiones.
3. Límite de cobertura semiabierto: ready requiere at_us<covered_until_us; el inicio del siguiente cuadro pendiente no está cubierto.
4. Un hilo no puede interrumpir native decode bloqueado: subproceso efímero PyAV-only, watchdog incluido arranque, terminate/join y lease/temporales controlados.
5. Descarga etiquetada requiere helper nuevo en apiClient/VideoExport, con validación de job/renderer/ruta; no reutilizar nativeVideo que apunta al MP4 antiguo.
6. Caja predicha y confianza de última medición deben distinguirse visiblemente de una detección real.

Estas son correcciones del diseño en borrador, no errores de implementación ni pruebas de producto fallidas.

## Validación mecánica ejecutada

| Revisión | Resultado |
|---|---|
| Esquemas JSON Schema2020-12 | 16 definiciones válidas |
| Ejemplos sintéticos conformes con formatos | 8 aprobados |
| Ejemplos inválidos rechazados | 8: índice negativo/bool, UUID inválido, propiedad extra, dirección both, coordenada fuera de rango, ID de imagen fabricado en preview y confianza fuera de rango |
| Referencias de esquemas | 37 resueltas, incluidas Error/VideoExportStatus legacy |
| Operaciones OpenAPI | 13, operationId únicos y parámetros path coherentes |
| Enlaces Markdown locales | Destinos existentes |
| Placeholders o decisiones bloqueantes | Ninguno |
| Alcance de requisitos/criterios de entrada | 24 FR y9 SC conservados; matriz de plan cubre los24 requisitos y los9 criterios |
| Código backend/frontend | Sin cambios |
| tasks.md | No creado; corresponde a speckit-tasks |

Las comprobaciones semánticas de PTS, pertenencia, sumas, TTL, revisión y geometría están documentadas para las pruebas de implementación; no se confunden con lo que JSON Schema puede demostrar.

## Constitution Check final

I: PASS, servicios/adaptadores/contratos separados. II: PASS, validación/errores/logs sin datos sensibles previstos. III: PASS, propietario/CSRF/leases/TTL y limpieza incluidos. IV: PASS de diseño, pruebas proporcionadas previstas con imagen/video y evidencia visual; no se declara aceptación de implementación. V: PASS de diseño, sin nuevo detector, reducers acotados y métricas separadas, comparación breve propuesta. Sin excepciones ni violaciones pendientes.

## Validaciones aún no ejecutadas

No se ejecutaron suites de producto, navegador, renderer, migraciones, OCR, video real, comparación de rendimiento ni prueba humana en esta fase. Los resultados que se exigirán durante implementación están en quickstart.md y plan.md. Los gates diferidos de009 permanecen pendientes; no se cierran desde010.
