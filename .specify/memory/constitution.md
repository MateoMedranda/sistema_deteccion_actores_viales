<!--
Sync Impact Report
- Version change: template (unversioned) -> 1.0.0
- Modified principles: template placeholders -> five project-specific principles
- Added sections: Security, Performance and Data Constraints; Development Workflow and Quality Gates
- Removed sections: none
- Follow-up TODOs: none
-->

# Sistema de detección de actores viales Constitution

## Core Principles

### I. Arquitectura modular y contratos explícitos
El sistema MUST mantenerse como un microservicio Python con FastAPI y separar la capa de API,
orquestación de inferencia, adaptadores de entrada, procesamiento de resultados y configuración.
Cada módulo MUST tener una única responsabilidad, interfaces tipadas y dependencias inyectables.
Las rutas HTTP MUST depender de contratos de servicio, no directamente del modelo de detección ni
del sistema de archivos. Esta separación permite sustituir el modelo aprobado, la fuente de video
o la interfaz de consumo sin introducir regresiones en el núcleo.

### II. Validación, errores y trazabilidad operativa
Toda entrada de imágenes, videos y flujos de cámara MUST validarse antes de su procesamiento:
tipo MIME, extensión, tamaño, decodificación, dimensiones y límites de duración o cuadros cuando
corresponda. La API MUST devolver errores HTTP consistentes, sin exponer rutas internas, secretos
ni detalles de implementación. Los eventos relevantes MUST registrarse mediante logs estructurados
con identificador de solicitud, fuente, duración y resultado de inferencia para permitir diagnóstico
reproducible.

### III. Seguridad y protección de datos por diseño
El microservicio MUST aplicar autenticación y autorización antes de aceptar fuentes de entrada o
exponer resultados; los secretos MUST obtenerse desde configuración segura y nunca desde el código
ni el repositorio. Las cargas MUST almacenarse temporalmente con nombres no predecibles y eliminarse
al terminar o expirar el trabajo. El acceso a cámaras, archivos, placas extraídas y resultados MUST
seguir el principio de mínimo privilegio. Los datos que permitan identificar vehículos o personas
MUST minimizarse, protegerse en tránsito y no conservarse más allá de la necesidad declarada.

### IV. Pruebas verificables y calidad del modelo
Cada cambio MUST incluir pruebas proporcionales al riesgo: unitarias para validadores, servicios y
transformaciones; de integración para rutas FastAPI y el contrato de inferencia; y de extremo a
extremo para al menos una imagen y un video de prueba controlados. Los cambios al modelo, sus pesos,
umbral de confianza o preprocesamiento MUST documentar el conjunto de evaluación, métricas y
comparación con la línea base aprobada. Ninguna modificación puede degradar deliberadamente los
criterios de detección acordados sin una decisión documentada.

### V. Rendimiento medible y uso eficiente de recursos
El diseño MUST evitar bloqueos innecesarios de la API, duplicación de decodificación y cargas
repetidas del modelo. Toda ruta de inferencia MUST medir latencia por solicitud, tiempo por cuadro,
uso de memoria y errores; los objetivos cuantitativos se definirán en cada especificación de
iteración según el hardware objetivo. La concurrencia, colas, muestreo de cuadros y aceleración de
hardware MUST justificarse con mediciones reproducibles. La velocidad de procesamiento no puede
comprometer la seguridad, la validez del resultado ni la estabilidad del servicio.

## Restricciones de seguridad, rendimiento y datos

- El stack principal MUST ser Python y FastAPI; las dependencias de visión por computador y el modelo
  de detección se declararán con versiones reproducibles.
- La API MUST exponer contratos versionados, documentación OpenAPI y límites configurables de carga,
  tiempo de espera y concurrencia.
- Los archivos entrantes se tratarán como no confiables: no se ejecutarán, no se confiará en su
  extensión y se rechazará cualquier archivo que no pueda decodificarse de forma segura.
- La configuración de modelo, umbrales, rutas temporales y credenciales MUST ser externa al código y
  diferenciar los entornos de desarrollo, prueba y producción.
- Las placas y demás características extraídas se consideran datos sensibles del dominio. Su
  visualización, persistencia, exportación o anonimización deberá estar explícitamente definida por
  la especificación de la funcionalidad correspondiente.
- El sistema MUST documentar el hardware, versión de modelo y parámetros usados para toda medición
  de rendimiento o calidad que se declare como evidencia.

## Flujo de desarrollo y puertas de calidad

1. Cada capacidad inicia con una especificación que defina usuarios, fuentes de entrada, escenarios,
   criterios de aceptación, restricciones de datos y métricas de éxito.
2. El plan técnico MUST identificar contratos API, módulos afectados, dependencias del modelo,
   estrategia de almacenamiento temporal, pruebas y mediciones de rendimiento.
3. Las tareas MUST ser pequeñas, ordenadas por dependencia y trazables a requisitos y criterios de
   aceptación. No se implementará una tarea que contradiga esta constitución.
4. Antes de declarar una iteración terminada, se MUST ejecutar la suite de pruebas pertinente,
   comprobar errores esperados, revisar logs y comparar las métricas establecidas con su línea base.
5. Todo cambio relevante MUST actualizar la documentación de API, configuración, modelo, métricas y
   decisión técnica. La auditoría de convergencia MUST registrar requisitos completados, pendientes,
   desviaciones y evidencia de verificación.

## Governance

Esta constitución prevalece sobre decisiones locales de implementación, planes y tareas. Cualquier
excepción requiere una justificación documentada, una evaluación de impacto en seguridad, calidad y
rendimiento, y su aprobación antes de incorporarse a una iteración.

Las enmiendas MUST actualizar este documento y el Sync Impact Report temporal. Los cambios que
eliminen o redefinan obligaciones se versionan como MAJOR; los nuevos principios o restricciones
materiales, como MINOR; y las aclaraciones sin cambio de obligación, como PATCH. Cada revisión de
plan, tareas, código y auditoría MUST comprobar cumplimiento de los principios aplicables.

**Version**: 1.0.0 | **Ratified**: 2026-10-21 | **Last Amended**: 2026-10-21
