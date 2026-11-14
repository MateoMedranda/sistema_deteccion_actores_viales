# Implementation Plan: Interfaz web prototipo vial

**Branch**: 005-interfaz-web-prototipo-vial | **Date**: 2026-11-14 | **Spec**: [spec.md](spec.md)

## Summary

Construir un demostrador local con React, Vite y TypeScript que consuma los contratos existentes de FastAPI para detección de imágenes, video asíncrono, conteo por línea y enriquecimiento. La interfaz mantiene en memoria la URL del backend y la API key, permite un solo video activo por sesión, consulta trabajos mediante polling y representa medios protegidos como Blob temporales. Se aplicarán dos ajustes de compatibilidad al backend: CORS con lista explícita de orígenes y DELETE para cancelar un trabajo de conteo. No se modificarán modelos de visión, inferencia ni almacenamiento permanente.

## Technical Context

**Language/Version**: TypeScript 5.x para frontend; Python 3.12 para ajustes mínimos del backend.

**Primary Dependencies**: React 18, Vite 5, @vitejs/plugin-react, Vitest, React Testing Library y Playwright; FastAPI 0.115, Pydantic Settings y pytest/httpx ya presentes.

**Storage**: Estado exclusivamente en memoria. Las URL Blob de imagen y video anotados se revocan al sustituirlas, reiniciar o desmontar. El backend conserva SQLite y artefactos con TTL; no se añadirá localStorage, cookies ni persistencia de frontend.

**Testing**: Vitest y React Testing Library para cliente HTTP, conversión de línea, componentes y estados; Playwright con API simulada para flujos de imagen, video y conteo; pytest de integración y contrato para CORS y cancelación de conteo.

**Target Platform**: Navegadores Chrome/Edge actuales en Windows 11; frontend estático. Backend FastAPI existente en Windows 11 o Linux x86_64.

**Project Type**: Aplicación web React separada que consume el microservicio FastAPI existente, con dos cambios mínimos de compatibilidad en backend.

**Performance Goals**: Mostrar confirmación de envío inmediatamente; actualizar estados cada 1–2 segundos sin solicitudes superpuestas; cumplir SC-001 (<2 minutos para imagen local); liberar Blob y detener polling en reinicio, desmontaje, vencimiento o estado terminal.

**Constraints**: Una API key, URL de backend, fuente y video activos por sesión; datos sensibles solo en memoria; X-API-Key en solicitudes protegidas; CORS explícito y nunca comodín con credenciales; artefactos anotados por fetch autenticado, no src directo; línea normalizada en [0,1] y no degenerada; sin móvil, cuentas, historial, exportación ni streaming.

**Scale/Scope**: Demostrador académico de una persona y un video activo. Reutiliza límites, TTL, propiedad por API key y concurrencia del backend. Varios videos simultáneos quedan como ampliación futura.

## Constitution Check

*GATE: PASS before Phase 0 research. Re-checked after Phase 1 design: PASS.*

| Principio | Diseño que asegura el cumplimiento |
|---|---|
| I. Arquitectura modular y contratos explícitos | ApiClient, sesión, dominios de imagen/video/conteo/enriquecimiento y componentes se separan; los cambios FastAPI permanecen detrás de rutas y configuración. |
| II. Validación, errores y trazabilidad | Se validan URL HTTP(S), archivos y línea; errores se traducen desde code, message y request_id sin mostrar cuerpos crudos ni clave. |
| III. Seguridad y protección de datos | API key, URL, IDs y placas viven solo en memoria; Blob protegido se revoca; CORS usa lista permitida configurable. |
| IV. Pruebas verificables y calidad del modelo | Pruebas de UI cubren casos correctos, terminales y errores; pytest verifica CORS y DELETE sin cambiar modelos ni pesos. |
| V. Rendimiento y recursos | Polling secuencial evita solapamientos; reinicio/desmontaje cancela y libera recursos; no se duplica inferencia. |

## Project Structure

### Documentation

```text
specs/005-interfaz-web-prototipo-vial/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── frontend-backend.md
└── tasks.md                 # generado después por speckit-tasks
```

### Source Code

```text
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── styles/
│   ├── components/
│   │   ├── SessionConfig.tsx
│   │   ├── ImageAnalysisPanel.tsx
│   │   ├── VideoJobPanel.tsx
│   │   ├── LineEditor.tsx
│   │   ├── CountJobPanel.tsx
│   │   ├── EnrichmentPanel.tsx
│   │   └── SafeStatus.tsx
│   ├── hooks/
│   │   ├── usePolling.ts
│   │   └── useObjectUrl.ts
│   ├── services/
│   │   ├── apiClient.ts
│   │   ├── apiTypes.ts
│   │   └── errorMapping.ts
│   ├── state/
│   │   └── demoSession.tsx
│   └── utils/
│       ├── lineCoordinates.ts
│       └── urlValidation.ts
└── tests/
    ├── unit/
    ├── component/
    └── e2e/

app/
├── api/routes/count_jobs.py       # DELETE de compatibilidad para conteo
├── core/config.py                 # orígenes CORS configurables
└── main.py                        # middleware CORS restringido

tests/
├── contract/test_count_jobs_contract.py
└── integration/
    ├── test_count_job_routes.py
    └── test_cors.py
```

**Structure Decision**: Se crea frontend/ como proyecto Vite independiente para que otro integrante pueda sustituir su presentación sin acoplarla al microservicio. El backend mantiene app/ y solo recibe CORS restringido y la cancelación faltante de conteo para satisfacer los contratos de sesión, seguridad y reinicio.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Segundo proyecto (frontend/) | React/Vite necesita construcción y pruebas independientes. | Servir HTML embebido desde FastAPI acoplaría presentación y microservicio. |
| Ajustes mínimos al backend | CORS y cancelación de conteo son necesarios para una interfaz de otro origen y FR-010. | Un proxy solo cubre desarrollo local y no permite cancelar conteos activos. |
