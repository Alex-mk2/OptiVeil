---
name: sdd_feature
description: >-
  Flujo Spec-Driven Development para implementar una FEATURE NUEVA en OptiVeil:
  spec → plan → tareas → implementación → verificación. Úsala siempre que el
  usuario quiera añadir o ampliar funcionalidad — un endpoint, un parámetro de
  escaneo, una métrica del motor evolutivo, un componente del frontend, una
  opción de la CLI — aunque no diga "feature" ni "SDD". Dispara con frases como
  "añade", "implementa", "quiero que también haga", "nueva ruta/endpoint",
  "nuevo campo", "soporta X". Para ARREGLAR algo que ya existe usa `sdd_bug_fix`
  en su lugar.
---

# SDD: Feature nueva en OptiVeil

Implementar una feature sin spec previa es la causa nº1 de retrabajo: se toca el
router equivocado, se rompe el otro estilo de import, o se mete lógica de
maximización en un motor que es estrictamente de minimización. Este flujo te
obliga a pensar antes de teclear. Avanza por fases y **no saltes a implementar
hasta tener spec y plan aprobados por el usuario**.

Antes de empezar, ten presente el contexto del repo: lee [CLAUDE.md](../../../CLAUDE.md)
y [.claude/context.md](../../context.md). Resumen de lo que más condiciona una feature:

- **NSGA-II = minimización, siempre.** Si la feature toca el motor evolutivo
  (`src/modules/stealth/nsga_II.py`, `src/core/engine.py`), las funciones de
  fitness se estructuran como minimización. Nunca maximización.
- **Dos estilos de import conviven.** La API importa `src.inter.xxx`; el engine
  hace `sys.path.append(.../src)` e importa `inter.xxx`. Un cambio de import debe
  seguir funcionando por ambos caminos (los tests cargan las dos raíces).
- **Autorización.** Cualquier operación sobre un target nuevo pasa por
  `enforce_scope(action, target)` de `src/core/scope.py` (registra en
  `results/audit.log`, lanza 403 fuera de scope).
- **Zero-trust y tipado estricto.** Validación de todo input; Pydantic en
  endpoints, interfaces TS en React.

## Fase 1 — Spec

El entregable de esta fase es un **archivo de spec numerado** en `docs/specs/`
(registro durable; que no se pierda con el tiempo). No es un documento
ceremonial: breve y al grano.

1. Calcula el siguiente ID: mira `docs/specs/`, toma el mayor `SPEC-NNNN` y suma 1
   (si no hay ninguno, `SPEC-0001`). La numeración es única para features y bugfixes.
2. Copia `docs/specs/_TEMPLATE.md` a `docs/specs/SPEC-NNNN-<slug>.md`, con `Tipo: feature`
   y `Estado: Borrador`.
3. Rellénala y **acuérdala con el usuario**. Responde en ella:

- **Qué** hace la feature y **por qué** (el problema que resuelve).
- **Criterios de aceptación**: cómo sabremos que está bien. En forma de
  comportamientos observables ("POST /api/x con body Y devuelve Z").
- **Alcance**: qué capas toca. Marca las que apliquen:
  - API (`src/api/routers/*`, `schemas.py`, `models.py`)
  - Motor / escaneo (`src/core/engine.py`, `src/modules/stealth/*`)
  - IA (`src/inter/*`, cliente en `llm_config.py`)
  - CLI (`src/IA_guard/cli.py`)
  - Frontend (`frontend/src/*`)
  - Persistencia (requiere migración Alembic)
- **Riesgos específicos**: ¿toca un target de red? → scope/auditoría. ¿toca
  fitness evolutivo? → minimización. ¿cambia un modelo de BD? → migración.

Para situarte rápido usa el grafo en vez de grep a ciegas:
`graphify query "<pregunta>"`, `graphify path "<A>" "<B>"`.

## Fase 2 — Plan

Traduce la spec a un plan de cambios concreto **antes de escribir código**:

- Lista los archivos a crear/editar, agrupados por capa.
- Si añades un endpoint: modelo Pydantic en `schemas.py`, router correspondiente,
  y `enforce_scope` si recibe un target.
- Si cambias un modelo SQLAlchemy: nueva revisión Alembic en
  `migrations/versions/` (`alembic revision --autogenerate -m "..."`).
- Si tocas imports compartidos: verifica el doble camino (API y engine).
- Define qué tests nuevos o ampliados demostrarán los criterios de aceptación.

Presenta el plan y espera visto bueno.

## Fase 3 — Tareas

Descompón el plan en pasos ordenados y pequeños, cada uno idealmente verificable
por un test. Implementa de dentro hacia afuera: primero el núcleo (engine/lógica),
luego la capa de exposición (router/CLI/frontend). Así cada paso se puede testear
sin depender de lo siguiente.

## Fase 4 — Implementación

- Respeta las reglas del repo (minimización, zero-trust, tipado, explícito sobre
  mágico — parámetros Scapy y routing explícitos).
- Escribe código que lea como el que lo rodea: misma densidad de comentarios,
  nombres e idioma del módulo que tocas.
- Tras modificar código, mantén el grafo al día: `graphify update .` (solo AST,
  sin coste).

## Fase 5 — Verificación

Los tests unitarios **no tocan PostgreSQL ni la red real** — ese es el contrato
del repo:

- BD: SQLite en memoria (ya fijado por `tests/conftest.py`).
- Endpoints: `fastapi.testclient.TestClient` (httpx).
- Scapy / LLM: **mockéalos**. Nunca lances paquetes reales ni llames a la API del
  LLM en un test. Mira los tests existentes como patrón (`tests/test_api.py`,
  `tests/test_offensive.py`, `tests/test_llm_config.py`).
- El fixture `_silence_audit_log` ya evita escrituras a `results/audit.log`.

Comandos:

```bash
pytest -ra                       # suite completa (lo que corre el CI en py3.12)
pytest tests/test_x.py::test_y   # el test concreto de tu feature
```

La feature está lista cuando: los criterios de aceptación de la Fase 1 tienen un
test que los demuestra, `pytest -ra` está verde, y el grafo está actualizado.
Reporta honestamente si algo quedó sin cubrir.

Al cerrar, actualiza la spec `docs/specs/SPEC-NNNN-*.md`: `Estado: Implementada`,
rellena la sección **Verificación** (tests y comandos) y los enlaces a commits/PR.
Añade/actualiza su fila en `docs/specs/README.md`. Así la spec refleja lo que de
verdad se construyó, no solo lo que se planeó.
