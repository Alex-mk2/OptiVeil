# SPEC-0004 — `/api/nmap` no pasa por `enforce_scope` ni audita

- **Tipo:** bugfix
- **Estado:** Implementada
- **Fecha:** 2026-10-25
- **Rama:** fix/nmap-enforce-scope
- **Rama base:** main
- **Autor:** Alex-mk2

## Problema
`POST /api/nmap` ejecuta la acción **más intrusiva** de la aplicación —`nmap -sV -O`
(detección de servicio/versión y de SO con paquetes reales)— pero **no comprueba el
scope ni deja traza en la auditoría**. Se le puede pasar cualquier IP en el cuerpo y
nmap sale a escanearla sin gating. Contradice la regla del proyecto ("solo mis
entornos autorizados") y el patrón del resto de endpoints ofensivos.

Reproducción (test): `POST /api/nmap` con `OPTIVEIL_SCOPE=10.0.0.0/8` y target
`8.8.8.8` (fuera de scope) **no** devolvía 403; llegaba a invocar nmap.

## Contexto
- `execute_nmap` en [src/api/routers/scanner.py](../../src/api/routers/scanner.py#L197)
  construye y lanza el comando directamente, sin llamar a `enforce_scope`.
- El resto de endpoints que tocan un target sí lo hacen: `start_scan`
  (`enforce_scope("scan", ...)`, [scanner.py:96](../../src/api/routers/scanner.py#L96))
  y `/api/validate` (scope estricto). `/api/nmap` era la excepción.
- `enforce_scope(action, target)` en [src/core/scope.py](../../src/core/scope.py#L87):
  audita siempre a `results/audit.log` y lanza **HTTP 403** si el objetivo está fuera
  de scope. Modo pasivo: **sin scope definido = permitido pero auditado** (uso en
  laboratorio), igual que `/api/scan`.
- Trampa del endpoint: `execute_nmap` termina en `except Exception as e: -> HTTPException(500)`.
  Como `HTTPException` es subclase de `Exception`, un `enforce_scope` colocado **dentro**
  del `try` degradaría el 403 a 500. Debe ir **antes** del `try`.

## Decisiones
- **Causa raíz:** `execute_nmap` nunca llamó a `enforce_scope`. El gating existía en el
  resto de endpoints ofensivos, pero este quedó sin cablear desde su creación.
- **Fix:** añadir `enforce_scope("nmap", str(req.target))` como **primera** sentencia de
  `execute_nmap`, fuera del `try`. Por qué fuera del try: evitar que el `except Exception`
  reempaquete el 403 como 500.
- **Modo pasivo (no estricto):** se usa `enforce_scope(action, target)` en su modo por
  defecto —sin scope definido = permitido + auditado—, **igual que `/api/scan`**. Por
  qué: nmap es un escaneo de red, hermano del de Scapy; debe recibir el mismo trato
  (flujo de laboratorio sin fricción, pero siempre auditado). Alternativa descartada:
  modo estricto (como `/api/validate`), que bloquearía el uso en lab sin scope; se
  reservó ese modo para la validación de explotabilidad, no para el escaneo.
- **Acción `"nmap"`** como etiqueta propia en el audit log, distinta de `"scan"`, para
  poder distinguir en la auditoría el escaneo nmap del escaneo Scapy del motor.

## Criterios de aceptación
1. `POST /api/nmap` con un target fuera del `OPTIVEIL_SCOPE` definido → **HTTP 403**,
   **sin** ejecutar nmap (no toca la red).
2. `POST /api/nmap` con un target en scope → el endpoint procede (ejecuta nmap).
3. La petición queda registrada en `results/audit.log` vía `enforce_scope` (acción
   `"nmap"`), como el resto de endpoints ofensivos.
4. La suite sigue verde en condiciones de CI.

## Alcance
- **API:** [src/api/routers/scanner.py](../../src/api/routers/scanner.py) (`execute_nmap`:
  una llamada a `enforce_scope` antes del `try`).
- **Tests:** `tests/test_scope.py` (403 fuera de scope sin invocar nmap; camino feliz
  en scope con `subprocess.run` mockeado).
- **Fuera:** la integración de la config de NSGA-II en el comando de nmap (el slider
  `stealth` hoy solo mapea a presets `-T0/-T2/-T3` y descarta `best_config`) queda para
  **SPEC-0005** (feature, rama aparte). El leak del `OPTIVEIL_SCOPE` del `.env` en la
  suite local lo arregla SPEC-0003 (`conftest.py`), aún sin mergear a `main`.

## Verificación
Implementada el 2026-10-25.
- `tests/test_scope.py::test_nmap_fuera_de_scope_devuelve_403` — reproducía el bug
  (antes: 500 tras ejecutar nmap; ahora: **403** sin tocar la red; el mock de
  `subprocess.run` lanza si se le llama).
- `tests/test_scope.py::test_nmap_en_scope_no_bloquea` — target en scope procede (200)
  con `subprocess.run` mockeado.
- Suite completa en condiciones de CI (scope vacío): **110 passed**
  (`OPTIVEIL_SCOPE="" OPTIVEIL_SCOPE_FILE="__no_scope_file__" pytest -ra`). En local sin
  esa env, 3 tests de scan/strategy fallan por el `.env` del dev (ver SPEC-0003), ajenos
  a este fix.

Cambios: `src/api/routers/scanner.py` (`enforce_scope("nmap", ...)` al inicio de
`execute_nmap`), `tests/test_scope.py` (2 tests de regresión).

## Enlaces
- Relacionada: [SPEC-0005](SPEC-0005-nmap-usa-nsga.md) (feature: nmap consume la config de NSGA-II).
