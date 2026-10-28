# OptiVeil — Bitácora de trabajo

> Estado volátil del proyecto. Arquitectura estable → CLAUDE.md. Estructura de
> código → `graphify query`. Esta bitácora → en qué vamos y por qué.

## Estado actual
- Rama: `feat/pareto-interactivo` (SPEC-0006), nacida de `main` al día.
- Tarea en curso: **SPEC-0006 — Frente de Pareto interactivo**. Implementada; `pytest -ra` 142 passed y `npm run build` OK. Pendiente: verificación manual del clic en la UI y merge a `main` (PR).
- Última cerrada: [SPEC-0005](../docs/specs/SPEC-0005-nmap-usa-nsga.md) (`/api/nmap` consume la config de NSGA-II en vez de presets `-T`) — **Implementada y mergeada a main** (2026-10-28), `pytest -ra` 132 passed.
- Anterior: [SPEC-0003](../docs/specs/SPEC-0003-validador-nuclei-timeout.md) (nuclei siempre daba `not_tested`) — Implementada. Fix: `-disable-update-check`/`-no-update-templates` + `-tags <servicio>`.
- Anterior: [SPEC-0002](../docs/specs/SPEC-0002-validacion-no-destructiva.md) (validación NO destructiva) — Implementada. Endpoint `/api/validate` con scope estricto; backend nuclei pluggable.
- Anterior: [SPEC-0004](../docs/specs/SPEC-0004-nmap-enforce-scope.md) (`/api/nmap` ahora pasa por `enforce_scope` y audita) — Implementada.
- Anterior: [SPEC-0001](../docs/specs/SPEC-0001-ruta-de-ataque-grafo.md) (ruta de ataque como grafo) — Implementada.

## Decisiones
- 2026-10-25 — Adoptado flujo SDD con skills propias `sdd_feature` y `sdd_bug_fix` (patrón spec→plan→tareas→implementación→verificación). Por qué: estandarizar el trabajo y respetar las reglas del repo (minimización NSGA-II, scope, doble import).
- 2026-10-25 — Instalado Graphify (`graphifyy`) en modo `--code-only`. Por qué: navegar el código sin releer todo y sin mandar datos del proyecto a un LLM externo (seguridad).
- 2026-10-25 — `graphify-out/` enviado a `.gitignore`. Por qué: `graph.json` se reescribe entero en cada build (diffs enormes) y se reconstruye en local.
- 2026-10-25 — Creada skill `project_memory` + esta bitácora. Por qué: persistir el estado de trabajo entre sesiones.
- 2026-10-25 — Registro durable de specs numeradas en `docs/specs/` (ADR + spec), gestionado por las skills SDD. Por qué: que problema/contexto/decisiones no se pierdan y cada feature/bug tenga un ID. Ver [índice](../docs/specs/README.md).
- 2026-10-25 — Añadida skill `disambiguate` como puerta de entrada para peticiones ambiguas (dilucida con evidencia del repo y deriva a sdd_feature/sdd_bug_fix). Por qué: evitar trabajar sobre la interpretación equivocada.
- 2026-10-25 — Regla: **una rama por feature/bug**, nacida de `main` actualizado (Fase 0 de las skills SDD). Si la tarea depende de código aún no mergeado, se basa en esa rama y se anota `Rama base:` en la spec. Por qué: cambios aislados, revisables y revertibles por separado.

## Pendientes
- [x] Commitear `.claude/` al control de versiones — hecho: está trackeado (skills + settings con hooks de graphify).
- [ ] **Veredicto de vulnerabilidad más claro** (duda de Alex, 2026-10-28). La
  validación (SPEC-0002/0003) ya da `confirmed/likely/not_confirmed/not_tested` +
  evidencia, pero se siente pobre porque: (1) se **descarta `info.severity`** de
  nuclei en `validator.py._map`; (2) no hay **síntesis ni prioridad por objetivo**
  (lista de estados, no "este objetivo: 1 crítico confirmado"); (3) `likely` es
  inferencia por versión, no prueba. Próxima spec tras SPEC-0006; posible combo
  con EPSS/KEV. Techo honesto: validación no destructiva = detección, no explotación.
- [ ] (Opcional) Montar el loop de evals del skill-creator si se quiere validar las skills SDD con métricas.
- [x] (Higiene) Podadas las ramas ya fusionadas (local y remoto). Solo queda `main`.

## Trampas conocidas
- Dos estilos de import conviven: API usa `src.inter.xxx`; engine usa `inter.xxx` vía `sys.path.append`. `tests/conftest.py` carga ambas raíces.
- Los tests NO tocan PostgreSQL ni red real: SQLite en memoria + mocks de Scapy/LLM.
- Hooks `PreToolUse` de graphify activos en `.claude/settings.json`: se ejecuta `graphify hook-guard` antes de Bash/Grep/Read/Glob.
