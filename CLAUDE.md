# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Al retomar el trabajo

Antes de releer el repo, lee [.claude/PROGRESS.md](.claude/PROGRESS.md): es la
bitácora con el estado volátil (en qué vamos, decisiones, pendientes). Para la
estructura del código usa `graphify query "..."` en vez de escaneos masivos. La
skill `project_memory` gestiona esa bitácora.

## Qué es OptiVeil

Framework de auditoría de red evolutiva + threat intelligence. Modela la configuración
de escaneo como un problema **multiobjetivo** (minimizar ruido/detección y tiempo) y usa
**NSGA-II** (`pymoo`) para producir un Frente de Pareto; el operador elige una solución
según el `stealth_level`. Sobre esa config escanea con **Scapy** (raw sockets), hace
fingerprinting y pasa los hallazgos por un LLM para análisis defensivo y generación de
ruta de ataque.

## Comandos

Backend (desde la raíz del repo):

```bash
pip install -r src/requirements.txt          # deps de ejecución
pip install pytest httpx pyyaml               # deps de test (o: pip install -e ".[test]")

uvicorn src.api.main:app --reload             # API en http://localhost:8000 (/docs)
optiveil audit <IP> --stealth <1-10> --ports <N>   # CLI (entry point de pyproject)
python src/IA_guard/cli.py audit <IP> --stealth 7 --ports 100   # equivalente sin instalar

alembic upgrade head                          # aplicar migraciones (necesita DATABASE_URL real)
```

Tests (los unitarios NO tocan PostgreSQL; usan SQLite en memoria):

```bash
pytest -ra                                    # suite completa
pytest tests/test_offensive.py                # un archivo
pytest tests/test_nsga.py::test_nombre        # un test concreto
```

El CI (`.github/workflows/ci.yml`) corre `pytest -ra` en Python 3.12 con
`DATABASE_URL=sqlite:///:memory:`. `conftest.py` ya fija ese default, así que los tests
corren sin configurar nada.

Frontend:

```bash
cd frontend && npm install && npm run dev     # http://localhost:5173
```

Docker (stack completo: Postgres + backend + frontend):

```bash
docker-compose up                             # requiere .env con POSTGRES_* definidos
```

## Arquitectura (el panorama)

Monolito modular: un repo con backend FastAPI, frontend React/Vite y una CLI Typer, todos
sobre el mismo núcleo en `src/`.

**Flujo central — `OptiVeilEngine.execute()` en [src/core/engine.py](src/core/engine.py).**
Esta es la columna vertebral; casi todo lo demás es entrada (API/CLI) o salida (reportes).
El orden importa:

1. `run_nsga_ii()` + `select_best_configuration(stealth_level)` → `modules/stealth/nsga_II.py`.
   Optimización multiobjetivo; devuelve una config (espera entre paquetes, nº de hilos, etc.).
2. `StealthScanner` (`modules/stealth/scanner.py`) → escaneo SYN con Scapy sobre esa config.
3. `ServiceIdentifier` (`inter/fingerprint.py`) → fingerprinting **en paralelo**
   (`ThreadPoolExecutor`) porque cada `identify()` puede bloquear hasta el timeout del socket.
4. LLM: `inter/IA_analyzer.py` (análisis defensivo) e `inter/IA_offensive.py`
   (ruta de ataque). Ambos clientes se construyen desde `inter/llm_config.py`.
5. Reportes: `utils/generate_report.py` (JSON + Markdown) y `utils/pareto_plot.py` (gráfica).

**Dos estilos de import conviven — no los "arregles" a ciegas.** La API importa como
`src.inter.xxx` / `src.api.xxx`. El engine y sus módulos hacen `sys.path.append(.../src)`
en runtime e importan como `inter.xxx`, `modules.stealth.xxx`, `utils.xxx`.
`tests/conftest.py` añade **ambas** raíces (`PROJECT_ROOT` y `src/`) al `sys.path` para que
los dos estilos funcionen en tests. Si cambias un import, verifica que no rompe el otro camino.

**API — [src/api/main.py](src/api/main.py)** monta cinco routers (`src/api/routers/`):
`scanner`, `strategy`, `reports`, `intelligence`, `persistence`. Modelos Pydantic en
`src/api/schemas.py`; modelos SQLAlchemy en `src/api/models.py`; sesión/engine de BD en
`src/api/database.py`.

**Autorización (scope) — [src/core/scope.py](src/core/scope.py).** Antes de operar sobre un
objetivo, los endpoints ofensivos llaman a `enforce_scope(action, target)`: carga el scope
(`OPTIVEIL_SCOPE` o `OPTIVEIL_SCOPE_FILE`/`scope.txt`), registra la petición en
`results/audit.log` (una línea JSON) y lanza **HTTP 403** si el objetivo está fuera de
alcance. **Sin scope definido no se restringe** (uso en laboratorio), pero igual se audita.
Si añades un endpoint que toque un target nuevo, pásalo por `enforce_scope`.

**Capa LLM — [src/inter/llm_config.py](src/inter/llm_config.py).** Punto único para el cliente
`ChatOpenAI` (LangChain). Proveedor por defecto OpenAI; token buscado en orden
`OPTIVEIL_AI_TOKEN` → `OPENAI_API_KEY`; `OPTIVEIL_AI_BASE_URL` para apuntar a otro proveedor
compatible (Azure AI Foundry, Ollama/LM Studio). `max_tokens` acota la salida (clave de
rendimiento en modelos locales). Si falta token lanza `LLMConfigError` para degradar con
mensaje claro. GitHub Models quedó retirado (30/07/2026): no reintroducir ese endpoint ni
`GITHUB_TOKEN`.

**Persistencia.** SQLAlchemy 2.x + Alembic (`migrations/versions/`). PostgreSQL en
producción/Docker; SQLite en memoria en tests. Config vía `DATABASE_URL`.

## Reglas del proyecto (de `.claude/context.md`)

- **NSGA-II = minimización, siempre.** Las funciones de fitness del motor evolutivo se
  estructuran SIEMPRE como minimización (detección, tiempo, tamaño de payload). Nunca
  implementar lógica de maximización en el motor evolutivo.
- **Validación paranoica (zero-trust).** No confiar en input externo ni en datos/logs de
  Scapy sin sanear. Validación estricta en todo pipeline, query y parsing.
- **Tipado estricto.** Pydantic en los endpoints FastAPI; interfaces TS en los componentes
  React.
- **Primeros principios, sin cajas negras.** Preferir configuración explícita (parámetros
  Scapy, routing de la API) sobre abstracciones mágicas.
- Antes de cambios estructurales en `src/`, verificar el impacto en los routers FastAPI.
  Al generar/modificar payloads de red, apilar bien las capas Scapy y manejar timeouts.

## Entorno (Windows)

Scapy necesita **Npcap** y **permisos de Administrador** para raw sockets. En Docker el
backend corre con `cap_add: NET_RAW, NET_ADMIN` (mínimo necesario, en vez de `privileged`).
Variables de entorno: copia `.env.example` a `.env`.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.
