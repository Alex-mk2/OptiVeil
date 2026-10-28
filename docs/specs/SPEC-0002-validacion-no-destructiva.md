# SPEC-0002 — Validación no destructiva de explotabilidad

- **Tipo:** feature
- **Estado:** Implementada
- **Fecha:** 2026-10-25
- **Rama:** perf/offensive-ai-speed
- **Autor:** Alex-mk2

## Problema
Hoy OptiVeil infiere explotabilidad por **versión + CVE** (`enrich_and_prioritize`
en `IA_offensive.py` adjunta CVEs del NVD y calcula un `priority` por CVSS). Pero
una versión vulnerable en el banner **no implica** que el servicio sea realmente
explotable (parches backported, config que mitiga, servicio no afectado). Eso
mete falsos positivos en el reporte y en la ruta de ataque. Falta un paso que
**confirme de forma no destructiva** que el hallazgo es realmente vulnerable,
elevando la confianza del resultado.

Uso previsto: **solo entornos propios del operador, con autorización**. La
seguridad de este uso no puede depender de la intención: hay que hornearla en el
gating técnico (ver Decisiones).

**Motivación real (del operador):** en pentest web (ZAP, reporte de
vulnerabilidades) surge siempre la pregunta "¿esto es explotable de verdad y cómo
lo demuestro?". El patrón que ya se usa a mano —p. ej. confirmar un *information
disclosure* pidiendo el endpoint con `curl` y mostrando la respuesta— es
justamente lo que esta feature automatiza: no solo un veredicto, sino **evidencia
reproducible** que sostenga el reporte. Esto orienta el backend hacia web/HTTP
(donde nuclei encaja) como primer foco.

## Contexto
- Priorización actual en [src/inter/IA_offensive.py](../../src/inter/IA_offensive.py)
  (`enrich_and_prioritize`, `finding_priority`).
- Guard de autorización en [src/core/scope.py](../../src/core/scope.py)
  (`enforce_scope`): hoy, **sin scope definido no restringe** (modo lab). Para
  acciones activas eso no vale.
- El repo ya invoca herramientas externas (`python-nmap`) y degrada con mensaje
  claro cuando falta configuración (patrón `LLMConfigError` en `llm_config.py`).

## Decisiones
- **Validación estrictamente NO destructiva.** Solo observación activa: enviar una
  petición benigna y leer la respuesta. Excluido por diseño: explotación real que
  obtenga ejecución, escritura/borrado de datos, DoS, fuerza bruta, cualquier cosa
  que cambie estado. Alternativa descartada: explotación/PoC real → es otro nivel
  (ver SPEC futura), con riesgo y guardrails distintos.
- **OptiVeil orquesta, no reimplementa exploits.** El motor de comprobación son
  plantillas/herramientas vetadas (p. ej. nuclei), no código de explotación propio.
- **Veredicto con grados, no booleano.** Cada hallazgo recibe
  `confirmed` (observación directa) | `likely` (heurística) | `not_confirmed` |
  `not_tested`, con evidencia. No colapsar `likely` en `confirmed`.
- **Gating técnico (lo que hace seguro el uso aunque el repo se filtre):**
  - Modo validación **opt-in, apagado por defecto**.
  - `enforce_scope` en modo **estricto** para esta acción: *sin scope definido =
    rechazar* (al revés que el modo pasivo). El target debe estar explícitamente
    en scope.
  - Auditoría de cada intento (`action="validate"`) en `results/audit.log`.
  - Timeouts y límite de concurrencia; nada masivo ni automático.
- **Zero-trust sobre la salida del validador externo**, igual que se sanea la del LLM.
- **El entregable es evidencia reproducible, no solo el veredicto.** Cada
  `confirmed`/`likely` incluye cómo reproducirlo (método + URL, equivalente al
  `curl` manual) y un fragmento de la respuesta que lo prueba.
- **La evidencia es sensible por definición** (puede contener los propios datos
  filtrados). Se **redacta y trunca**, y no se escribe en artefactos versionados
  (reportes en git, audit log): el audit log guarda que se validó y el veredicto,
  no el contenido sensible. Coherente con el endurecimiento de credenciales.

## Criterios de aceptación
1. Con el modo validación **apagado** (default), el comportamiento actual no cambia.
2. Con validación activada y un target **en scope**, cada hallazgo devuelve un
   `validation` con `status` (confirmed/likely/not_confirmed/not_tested) y evidencia.
3. Validación activa con **scope no definido o target fuera** → rechazada (403) y
   registrada en el audit log. (Gating estricto, distinto del modo pasivo.)
4. Si el backend de validación no está disponible, se degrada con mensaje claro
   (`not_tested`), sin romper la respuesta.
5. Ninguna comprobación modifica estado del objetivo (no destructivo, verificable
   por el catálogo de checks documentado).
6. Un `confirmed`/`likely` incluye **evidencia reproducible** (método + URL para
   rehacerlo y un fragmento de respuesta), con los datos sensibles **redactados/
   truncados** y nunca escritos en artefactos versionados ni en el audit log.

## Alcance
- **Core/IA:** nuevo módulo de validación (interfaz `Validator` + un backend) en
  `src/inter/` o `src/core/`. Sanea e interpreta la salida del backend.
- **Autorización:** `scope.py` — variante estricta de `enforce_scope` (p. ej.
  `enforce_scope(..., strict=True)`: sin scope = 403).
- **API:** `schemas.py` (`ValidationResult`), endpoint o flag opt-in (p. ej.
  `/api/validate` o `validate=false` por defecto).
- **Frontend:** badge de estado de validación por hallazgo.
- **Tests:** backend de validación **mockeado** (nunca red real); gating estricto
  de scope; grados de veredicto; default apagado; degradación sin backend.
- **Fuera:** explotación real / PoC con ejecución (otra spec); motor evolutivo; BD.

## Backend elegido
Interfaz `Validator` **pluggable** con **nuclei** como primer backend (plantillas
de detección, acotadas a tags no intrusivos). Por qué: valor real rápido sin atar
el diseño a una sola herramienta; mañana se añade otro backend (sondas propias)
sin tocar la API ni el frontend. La dependencia del binario nuclei se degrada con
mensaje claro (`not_tested`) si no está instalado.

## Verificación
Implementada el 2026-10-25. `pytest -ra` → **121 passed** (13 nuevos en
`tests/test_validator.py`); eslint limpio en los archivos de frontend tocados.
Cubierto:
- `redact_snippet`: enmascara secretos (password/token/...) y trunca.
- `NucleiValidator` con runner inyectado (sin red): match directo → `confirmed`,
  match por versión → `likely`, sin match → `not_confirmed`; `_parse` ignora
  líneas no-JSON; backend ausente/error → `not_tested`.
- Gating estricto en el endpoint `/api/validate`: sin scope o fuera de scope →
  403; en scope → 200 (con `scope.load_scope` mockeado para determinismo).
- Evidencia redactada: el secreto extraído no aparece en el snippet.

Cambios: `src/core/scope.py` (`strict` en `is_in_scope`/`enforce_scope`),
`src/inter/validator.py` (interfaz `Validator` + `NucleiValidator` + saneo/
redacción), `src/api/schemas.py` (`ValidationRequest`/`ValidationResult`),
`src/api/routers/validation.py` (endpoint), `src/api/main.py` (registro),
`frontend/src/...` (servicio + badge + botón opt-in). Frontend sin cobertura
pytest (verificación visual pendiente al levantar el dev server).

## Enlaces
- Relacionada: [SPEC-0001](SPEC-0001-ruta-de-ataque-grafo.md) (consume la priorización que esto valida).
