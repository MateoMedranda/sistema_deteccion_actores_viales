# Validación de implementación008

Baseline congelada desde c4857a1 en baseline.json y tests/fixtures/video_presentation/legacy_renderer.py. El archivo generado tsconfig.tsbuildinfo previo se conserva por separado y queda fuera de commits.

## Registro

- Checklist requirements.md:16/16, solo lectura.
- Frontend previo:28 archivos/78 pruebas PASS.
- Backend previo:253 pruebas PASS (51.04s).
- Fixtures008:10 escenas (3densas) y6clips sintéticos,2densos con21actores;3segmentos de150cuadros. Manifiesto/raw/referencias congelados antes de evaluar la candidata.
- Los fixtures verifican presentación/lifecycle; no certifican precisión real de detector/OCR.

Pendientes externos conservados:006/T067–T068 y007/T061–T064/T070. Los gates de coste completo, fluidez, geometría y revisión visual se registrarán con sus medidas efectivas.

## US1
T001–T012 completadas. Vitest:2 pruebas nuevas PASS (tabs/TTL oculto), build PASS; Playwright:3 recorridos PASS en360/768/1440 y texto200%, sin nuevas operaciones por navegar. Transporte manual se conserva temporalmente hasta US2.

## US2
T013–T027 completadas. Gateway separado con sesiones RAM/CSRF/allowlist/cotas/Range y web-policy autenticada; cliente directo conservado.11 pruebas backend de gateway/política PASS;2 pruebas de transporte/reset frontend PASS y build PASS. Playwright009:9 recorridos de sesión/imagen/navegación PASS en3tamaños, sin X-API-Key en solicitudes del navegador. Los límites de streams/ingreso local/privado se conservan; despliegue público no habilitado.
