# OptiVeil — Bitácora de trabajo

> Estado volátil del proyecto. Arquitectura estable → CLAUDE.md. Estructura de
> código → `graphify query`. Esta bitácora → en qué vamos y por qué.

## Estado actual
- Rama: `perf/offensive-ai-speed` — acelerar la IA ofensiva (sin doble generación, salida acotada por `max_tokens`).
- Tarea en curso: ninguna. Última cerrada: [SPEC-0001](../docs/specs/SPEC-0001-ruta-de-ataque-grafo.md) (ruta de ataque como grafo) — **Implementada**, `pytest -ra` 108 passed.

## Decisiones
- 2026-10-25 — Adoptado flujo SDD con skills propias `sdd_feature` y `sdd_bug_fix` (patrón spec→plan→tareas→implementación→verificación). Por qué: estandarizar el trabajo y respetar las reglas del repo (minimización NSGA-II, scope, doble import).
- 2026-10-25 — Instalado Graphify (`graphifyy`) en modo `--code-only`. Por qué: navegar el código sin releer todo y sin mandar datos del proyecto a un LLM externo (seguridad).
- 2026-10-25 — `graphify-out/` enviado a `.gitignore`. Por qué: `graph.json` se reescribe entero en cada build (diffs enormes) y se reconstruye en local.
- 2026-10-25 — Creada skill `project_memory` + esta bitácora. Por qué: persistir el estado de trabajo entre sesiones.
- 2026-10-25 — Registro durable de specs numeradas en `docs/specs/` (ADR + spec), gestionado por las skills SDD. Por qué: que problema/contexto/decisiones no se pierdan y cada feature/bug tenga un ID. Ver [índice](../docs/specs/README.md).
- 2026-10-25 — Añadida skill `disambiguate` como puerta de entrada para peticiones ambiguas (dilucida con evidencia del repo y deriva a sdd_feature/sdd_bug_fix). Por qué: evitar trabajar sobre la interpretación equivocada.

## Pendientes
- [ ] Decidir si se commitea `.claude/` (skills + settings con hooks de graphify) al control de versiones.
- [ ] (Opcional) Montar el loop de evals del skill-creator si se quiere validar las skills SDD con métricas.

## Trampas conocidas
- Dos estilos de import conviven: API usa `src.inter.xxx`; engine usa `inter.xxx` vía `sys.path.append`. `tests/conftest.py` carga ambas raíces.
- Los tests NO tocan PostgreSQL ni red real: SQLite en memoria + mocks de Scapy/LLM.
- Hooks `PreToolUse` de graphify activos en `.claude/settings.json`: se ejecuta `graphify hook-guard` antes de Bash/Grep/Read/Glob.
