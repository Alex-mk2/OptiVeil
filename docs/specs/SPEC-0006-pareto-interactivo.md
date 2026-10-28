# SPEC-0006 — Frente de Pareto interactivo

- **Tipo:** feature
- **Estado:** Implementada
- **Fecha:** 2026-10-28
- **Rama:** feat/pareto-interactivo
- **Autor:** Alex Mellado

## Problema
Lo más original de OptiVeil —optimizar el escaneo como problema multiobjetivo y
producir un Frente de Pareto (ruido vs. tiempo)— hoy queda oculto tras un slider
`stealth` 1–10. El operador no elige una solución del frente: elige un número, y
`select_best_configuration` lo traduce a un punto por percentil. El frente real
(`ParetoVisualization.jsx`) solo se ve **después** de escanear y es de solo
lectura. No se puede explorar el compromiso ni clicar la solución deseada.

## Contexto
- `run_nsga_ii(target_ports)` → `(X, F)`; **el frente depende solo del nº de
  puertos, no de la IP**, y está cacheado ([nsga_II.py:36](../../src/modules/stealth/nsga_II.py#L36)).
- `select_best_configuration(X, F, stealth_level)` devuelve `{config, pareto_front}`,
  donde `pareto_front` es una lista de `{noise, time}` **sin la config de cada
  punto** ([nsga_II.py:62](../../src/modules/stealth/nsga_II.py#L62)).
- El escaneo se lanza con `ScanRequest {target, stealth, ports}`
  ([schemas.py:72](../../src/api/schemas.py#L72)); `scanner.start_scan` deriva la
  config desde `stealth` ([scanner.py:213](../../src/api/routers/scanner.py#L213)).
- El frente ya viaja al frontend dentro de los resultados y se pinta en
  `ParetoVisualization.jsx`, con el punto elegido resaltado
  ([IntelligenceResults.jsx:177](../../frontend/src/components/IntelligenceResults.jsx#L177)).
- Reglas que condicionan: NSGA-II = **minimización** (no se toca el fitness);
  **zero-trust** en todo input; Pydantic en endpoints e interfaces TS en React.

## Decisiones
- **Decisión:** exponer el frente con un endpoint propio
  `GET /api/strategy/pareto?ports=N` que devuelve cada punto **con su config
  decodificada** (`wait_time_ms`, `packet_size`, `threads`) además de
  `noise`/`time`. **Por qué:** el frente no depende del target, así el operador lo
  explora *antes* de escanear sin tocar la red. **Alternativa descartada:** que
  el frente solo venga tras el escaneo (lo actual) — no permite elegir antes de
  comprometer un escaneo.
- **Decisión:** el punto elegido se envía al escaneo como **config explícita**
  (campo opcional `config` en `ScanRequest`), no como un índice al frente.
  **Por qué:** NSGA-II no fija semilla → el frente no es determinista entre
  procesos y la caché puede enfriarse; un índice sería frágil y podría apuntar a
  otro punto. La config explícita es autocontenida. **Alternativa descartada:**
  `pareto_index` — frágil ante recálculo/caché fría.
- **Decisión (zero-trust):** si llega `config`, cada campo se valida contra los
  **rangos del problema** (`OptiVeilSthealthProblem`) antes de escanear; fuera de
  rango → 422. **Por qué:** evitar que un cliente inyecte una config arbitraria
  no-óptima o peligrosa; solo se aceptan valores dentro del espacio que NSGA
  optimiza.
- **Decisión:** `stealth` se mantiene como atajo. Si `config` viene, manda
  `config`; si no, se comporta **exactamente como hoy** (no-regresión). El slider
  del frontend resalta el punto equivalente del frente.
- **Decisión:** capar `ports` a `le=65535` tanto en el endpoint del frente como
  en `ScanRequest`. **Por qué:** `ScanRequest.ports` hoy es `Field(100, ge=1)`
  **sin tope superior** → hueco zero-trust preexistente (un `ports` enorme dispara
  NSGA de 100 generaciones + un escaneo gigante). Se tapa de paso. 65535 es el
  máximo real de puerto TCP.

## Criterios de aceptación
1. `GET /api/strategy/pareto?ports=100` → 200 con
   `{pareto_front: [{index, noise, time, config:{wait_time_ms, packet_size, threads}}, …]}`,
   lista no vacía y ordenada por `noise` ascendente; los `noise`/`time` coinciden
   con los que produce `run_nsga_ii(100)`.
2. `ports` ausente, no entero, `< 1` o `> 65535` → 422 (no 500), tanto en
   `GET /api/strategy/pareto` como en `POST /api/scan`.
3. `POST /api/scan` con un `config` **válido** → el escaneo usa esa config y la
   respuesta la refleja en `best_config` (no la derivada de `stealth`).
4. `POST /api/scan` con un `config` **fuera de rango** → 422 y **no** se escanea.
5. `POST /api/scan` **sin** `config` → comportamiento idéntico al actual (`stealth`
   manda). *(no-regresión; cubre también CLI y llamadas existentes)*
6. Frontend: con target + puertos indicados, el operador ve el frente y puede
   **clicar un punto**; el punto seleccionado muestra su config y es la que se usa
   al lanzar el escaneo. El slider `stealth` sigue funcionando y resalta el punto
   equivalente.

## Alcance
- **API:** `src/api/schemas.py` (nuevos `ScanConfig`, `ParetoPoint`,
  `ParetoFrontResponse`; `config: ScanConfig | None` en `ScanRequest`),
  `src/api/routers/strategy.py` (endpoint del frente) y
  `src/api/routers/scanner.py` (usar `config` si viene; validar rangos).
- **Motor:** `src/modules/stealth/nsga_II.py` — helper **de solo lectura** que
  empareja `X`↔`F` en puntos con config y expone los rangos del problema. **No se
  toca el fitness ni la lógica de minimización.**
- **Frontend:** `frontend/src/components/ParetoVisualization.jsx` (puntos
  clicables + selección), `IntelligenceResults.jsx` / `AuditDashboard.jsx` y
  `services/api.js` (obtener el frente y mandar `config` al escanear).
- **Fuera de alcance:** persistencia/migraciones (ninguna), CLI (sigue con
  `stealth`), nuevos tipos de escaneo (es SPEC-0007).
- **Scope/auditoría:** el endpoint del frente **no toca ningún target** (depende
  solo de `ports`), por eso no pasa por `enforce_scope`. El escaneo sigue
  pasando por `enforce_scope` igual que hoy (sin cambios).

## Verificación
`pytest -ra` → **142 passed**. Tests nuevos:
- `tests/test_pareto.py`:
  - `test_pareto_endpoint_devuelve_frente_con_config` (criterio 1: frente con
    config por punto, ordenado por ruido; NSGA mockeado).
  - `test_pareto_ports_invalido_422` (criterio 2: `ports` 0/-1/70000 → 422).
  - `test_pareto_front_with_configs_ordena_y_adjunta_config` y
    `test_metrics_for_config_usa_la_formula_del_problema` (helpers del motor).
  - `test_scanconfig_bounds_espejo_de_config_bounds` (ata `ScanConfig` a
    `CONFIG_BOUNDS`: sin deriva de rangos).
- `tests/test_api.py`:
  - `test_scan_rechaza_config_fuera_de_rango` (criterio 4: `config` fuera de rango → 422).
  - `test_scan_pasa_config_explicita_al_motor` (criterio 3: el motor recibe la `config`).
  - `test_scan_sin_config_no_regresiona` (criterio 5: sin `config`, flujo intacto).

Frontend: `npm run build` OK (compila sin errores). **Criterio 6 (clic en el
frente desde la UI) pendiente de verificación manual** levantando la app — no hay
infra de test JS en el repo.

## Enlaces
- Opción A del roadmap (la otra mitad → SPEC-0007, más tipos de escaneo).
- Relacionadas: SPEC-0005 (`/api/nmap` ya consume la config de NSGA-II).

## Preguntas abiertas (resueltas 2026-10-28)
1. **Exploración pre-escaneo** — SÍ. El frente se obtiene y se clica antes de
   escanear (no depende de la IP, es gratis).
2. **Slider `stealth`** — SE MANTIENE como atajo que resalta el punto equivalente
   (compatibilidad con CLI y `/api/nmap`/SPEC-0005; entrada guiada al frente).
3. **Tope de `ports`** — `le=65535` en **ambos** sitios (endpoint del frente y
   `ScanRequest`), tapando el hueco zero-trust preexistente.
