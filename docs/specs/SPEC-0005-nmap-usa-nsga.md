# SPEC-0005 — `/api/nmap` consume la config de NSGA-II en vez de presets `-T`

- **Tipo:** feature
- **Estado:** Implementada
- **Fecha:** 2026-10-25
- **Rama:** feature/nmap-usa-nsga
- **Rama base:** main
- **Autor:** Alex-mk2

## Problema
`/api/nmap` ignora el motor evolutivo. El slider `stealth` (1-10) se colapsa a
**tres presets de timing de nmap** (`-T0`/`-T2`/`-T3`, [scanner.py](../../src/api/routers/scanner.py#L203)),
así que mover el slider de 1 a 4 no cambia nada y de 8 a 10 tampoco. El sigilo
que presenta ese tab es **cosmético**: no es la configuración Pareto-óptima que
calcula NSGA-II (espera entre paquetes, paralelismo). Eso contradice la tesis del
proyecto —optimización multiobjetivo del sigilo— y deja a nmap como un escáner
paralelo sin relación con el motor.

El diseño pretendido era que **la salida de NSGA-II alimentara a nmap**; nunca se
cableó.

## Contexto
- El motor expone, igual que usa `OptiVeilEngine.execute()`
  ([engine.py:28-30](../../src/core/engine.py#L28)):
  - `run_nsga_ii(target_ports) -> (X, F)` (cacheado con `lru_cache` por nº de puertos).
  - `select_best_configuration(X, F, stealth_level) -> {"config": {...}, "pareto_front": [...]}`
    donde `config = {wait_time_ms: float[10..5000], packet_size: int[64..1500], threads: int[1..10], metrics}`.
- `execute_nmap` ([scanner.py:197](../../src/api/routers/scanner.py#L197)) ya pasa por
  `enforce_scope("nmap", target)` (SPEC-0004) y construye el comando a mano.
- nmap acepta como flags explícitos los mismos conceptos del motor:
  - `wait_time_ms` → `--scan-delay <N>ms` (espera entre sondas). Mapeo directo.
  - `threads` → `--max-parallelism <N>` (sondas en paralelo). Mapeo directo.
  - `packet_size` → `--data-length <N>` solo añade **relleno aleatorio**, no fija el
    tamaño real del paquete. Semántica distinta.
- `ScanRequest`: `stealth int[1..10]`, `ports int>=1`, `target IPvAnyAddress` (ya validado).

## Decisiones
- **Mapeo elegido:** `wait_time_ms → --scan-delay <N>ms` y `threads → --max-parallelism <N>`,
  derivados de `select_best_configuration(run_nsga_ii(ports), stealth)`. Se **eliminan**
  los `-T0/-T2/-T3`. Por qué: un `-T` fija su propio timing (delay, paralelismo,
  timeouts) y **pelearía** con un `--scan-delay`/`--max-parallelism` explícitos;
  además lo explícito sobre lo mágico es regla del repo.
- **`packet_size` SÍ se mapea** → `--data-length <N>`. Por qué: la premisa del
  proyecto es que **todos** los parámetros que optimiza NSGA-II los ejecute nmap;
  dejar fuera `packet_size` rompería esa premisa. Matiz honesto: `--data-length` es
  relleno **aditivo** (añade N bytes de datos aleatorios a cada sonda), no fija el
  tamaño total del paquete; aun así es el único knob de nmap que hace que la dimensión
  `packet_size` del motor **afecte el tráfico real**. Se documenta como aproximación.
- **La config se calcula en el router**, llamando directo a `run_nsga_ii` +
  `select_best_configuration` (mismo patrón que el engine), no instanciando el engine
  entero (que además escanearía con Scapy). Cacheado por `lru_cache`: la primera
  corrida por nº de puertos paga la optimización; las siguientes son instantáneas.
- **Visibilidad:** la respuesta incluye la config aplicada (`nsga_config` con
  `scan_delay_ms`, `max_parallelism`, y las métricas de ruido/tiempo), para que el
  frontend/usuario vea que el sigilo es el del motor y no un preset.
- **Zero-trust/tipado:** `stealth`/`ports` ya los valida Pydantic; los valores de
  NSGA se formatean como **enteros** al construir el argv (lista, nunca shell), así no
  hay inyección. `enforce_scope` se mantiene (regresión de SPEC-0004).
- **Minimización intacta:** esta feature solo **consume** la config; no toca las
  funciones de fitness del motor. Nada de maximización.

## Criterios de aceptación
1. `POST /api/nmap` construye un comando con `--scan-delay <N>ms`,
   `--max-parallelism <N>` y `--data-length <N>` derivados de la `best_config` de
   NSGA-II, y **sin** `-T0/-T2/-T3`.
2. Al variar `stealth`, el `--scan-delay` y `--max-parallelism` cambian conforme a la
   selección del Frente de Pareto (más sigilo → más espera / menos paralelismo).
3. La respuesta incluye la config NSGA aplicada (`nsga_config`).
4. `enforce_scope("nmap", target)` sigue bloqueando fuera de scope (403), antes de
   calcular NSGA ni tocar la red.
5. `pytest -ra` verde.

## Alcance
- **API:** [src/api/routers/scanner.py](../../src/api/routers/scanner.py) (`execute_nmap`:
  calcular config NSGA, mapear a flags, quitar `-T`, enriquecer respuesta).
- **Tests:** `tests/test_scope.py` o nuevo `tests/test_nmap_nsga.py` (mock de
  `run_nsga_ii`/`select_best_configuration` y captura del argv con `subprocess.run`
  mockeado; assert de flags y ausencia de `-T`; que `enforce_scope` siga primero).
- **Fuera:** renombrar/ajustar el slider en el frontend (opcional, otra tarea);
  el motor evolutivo (solo se consume); BD.

## Verificación
Implementada el 2026-10-25. Tests en `tests/test_nmap_nsga.py` (mock de
`run_nsga_ii`/`select_best_configuration` + `subprocess.run` que captura el argv,
sin red):
- `test_nmap_mapea_config_nsga_a_flags` — la `best_config` se mapea a
  `--scan-delay 251ms` (round de 250.6), `--max-parallelism 3`, `--data-length 512`.
- `test_nmap_sin_presets_de_timing` — el comando ya **no** incluye ningún `-T0..-T5`.
- `test_nmap_respuesta_incluye_config_nsga` — la respuesta expone `nsga_config`.
- `test_nmap_reenvia_puertos_y_stealth_al_motor` — el router pasa `ports` a
  `run_nsga_ii` y `stealth` a `select_best_configuration`.
- `test_nmap_fuera_de_scope_no_calcula_nsga` — `enforce_scope` corta con 403 antes de
  invocar al motor y a nmap (regresión de SPEC-0004).

Suite completa en condiciones de CI (scope vacío): **115 passed**
(`OPTIVEIL_SCOPE="" OPTIVEIL_SCOPE_FILE="__no_scope_file__" pytest -ra`). En local sin
esa env, los 3 tests de scan/strategy fallan por el `.env` del dev (lo aísla SPEC-0003,
aún sin mergear a `main`), ajenos a esta feature.

Cambios: `src/api/routers/scanner.py` (`execute_nmap`: import del motor, cálculo de
config NSGA, mapeo a `--scan-delay`/`--max-parallelism`/`--data-length`, se quitan los
`-T`, respuesta con `nsga_config`), `tests/test_nmap_nsga.py` (nuevo).

## Enlaces
- Depende de: [SPEC-0004](SPEC-0004-nmap-enforce-scope.md) (el `enforce_scope` de nmap).
