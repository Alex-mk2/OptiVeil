# SPEC-0003 — El validador nuclei siempre degrada a `not_tested`

- **Tipo:** bugfix
- **Estado:** Implementada
- **Fecha:** 2026-10-25
- **Rama:** fix/validator-scope-templates
- **Rama base:** perf/offensive-ai-speed (el código de SPEC-0002 aún no está en `main`)
- **Autor:** Alex-mk2

## Problema
El validador de explotabilidad (SPEC-0002) **nunca devuelve `confirmed`/`likely`**
contra un target real: todos los hallazgos salen `not_tested`. Reproducido en
Docker con nuclei v3.11.1 ya instalado y un target en scope: los badges del
frontend quedaron todos en **"NO PROBADO"**.

Reproducción manual dentro del contenedor:
```
nuclei -u 127.0.0.1 -jsonl -silent -etags dos,intrusive,... -timeout 10
# DURACION=198s  (supera el timeout de 120s del subprocess → TimeoutExpired)
```

## Contexto
- `NucleiValidator._run_nuclei` en [src/inter/validator.py](../../src/inter/validator.py)
  lanza nuclei **sin acotar plantillas** (corre el catálogo entero, miles) y con
  `subprocess.run(..., timeout=120)`.
- `validate()` captura cualquier excepción y degrada a `NOT_TESTED`
  ([validator.py:112](../../src/inter/validator.py#L112)), así que el
  `TimeoutExpired` se traga en silencio y el usuario solo ve "NO PROBADO".
- Medición en contenedor: catálogo completo ≈198s; acotado por `-tags ftp,smtp`
  **y** con el update-check desactivado ≈**0s** (y con match).

## Decisiones
- **Causa raíz (doble):** (1) nuclei hace un **chequeo/actualización de plantillas
  contra GitHub en cada invocación** (red), que estanca la corrida; (2) se lanza
  el **catálogo completo** sin filtrar por el servicio del hallazgo. Juntos
  superan el timeout de 120s → `TimeoutExpired` → `not_tested` siempre.
- **Fix:** en el comando de nuclei (a) `-disable-update-check` y
  `-no-update-templates` (sin red en caliente, sin estancamiento); (b) acotar con
  `-tags <servicio>` derivado de los hallazgos, para correr solo lo pertinente.
  Por qué: alinea con la spec (evidencia *enfocada* por finding) y lo vuelve
  rápido. Alternativa descartada: solo subir el timeout → espera de minutos y
  ruido inútil (plantillas HTTP contra FTP/SMTP); no ataca la causa.
- **Zero-trust:** el `service` viene del fingerprint (input no confiable). Se
  **sanea** a `[a-z0-9-]` antes de pasarlo como tag.
- **Degradación honesta:** si ningún servicio del lote mapea a un tag, no se corre
  el catálogo entero; se devuelve `not_tested` con motivo, en vez de un
  `not_confirmed` engañoso ("se probó y no hay nada") cuando en realidad no se probó.
- **Contrato del runner:** pasa de `runner(target)` a `runner(target, tags)` para
  que el backend reciba el acotado. Afecta solo a la inyección en tests.

## Criterios de aceptación
1. El comando de nuclei se **acota por `-tags`** al/los servicio(s) del lote
   (no corre el catálogo completo).
2. El comando incluye `-disable-update-check` y `-no-update-templates`.
3. Un servicio no mapeable (vacío/no saneable) → `not_tested` **sin** invocar
   nuclei, con motivo en la evidencia.
4. El `service` se sanea: caracteres fuera de `[a-z0-9-]` no llegan al comando.
5. La suite sigue verde (los grados confirmed/likely/not_confirmed/not_tested y
   el gating de scope no cambian de comportamiento).

## Alcance
- **IA:** [src/inter/validator.py](../../src/inter/validator.py) (`NucleiValidator`:
  derivación de tags + flags del comando + contrato del runner).
- **Tests:** `tests/test_validator.py` (regresión del acotado y los flags; saneo;
  degradación sin tag; actualización de runners inyectados a la nueva firma).
- **Fuera:** afinar el set de plantillas para servicios HTTP (un `-tags http`
  sigue siendo amplio; queda como mejora futura), motor evolutivo, BD, frontend.

## Verificación
Implementada el 2026-10-25. `pytest -ra` → **125 passed** (4 nuevos en
`tests/test_validator.py`). Cubierto:
- Regresión del bug: el comando se acota por `-tags <servicio>` (sin él, nuclei
  corría el catálogo entero) e incluye `-disable-update-check` /
  `-no-update-templates`.
- Saneo zero-trust del `service` (caracteres fuera de `[a-z0-9-]` no llegan al
  comando).
- Servicio no mapeable → `not_tested` sin invocar nuclei, con motivo.
- Medición real en contenedor: corrida acotada ≈**0s** (antes ≈198s → timeout).

Cambios: `src/inter/validator.py` (`_service_tags`, flags del comando, contrato
del runner `runner(target, tags)`), `tests/test_validator.py` (regresión +
actualización de runners inyectados), `tests/conftest.py` (aísla los tests del
`OPTIVEIL_SCOPE` del `.env` del desarrollador; antes un scope local rompía con
403 los tests de escaneo/estrategia).

## Enlaces
- Corrige: [SPEC-0002](SPEC-0002-validacion-no-destructiva.md).
