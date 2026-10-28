# SPEC-0007 — Buscar rutas que exponen información sensible (con evidencia)

- **Tipo:** feature
- **Estado:** Implementada
- **Fecha:** 2026-10-28
- **Rama:** feat/veredicto-explotabilidad
- **Rama base:** main
- **Autor:** Alex Mellado

## Problema
El objetivo del operador no es una etiqueta `confirmed/likely`, sino **reportar
con evidencia dónde y cómo** un objetivo filtra lo que no debería: **rutas/endpoints
HTTP que exponen información sensible** (un directorio listable, un `.env`/`.git`
accesible, un backup, o un endpoint de la app que devuelve datos personales —p. ej.
RUTs— sin autenticación). Hoy OptiVeil no busca eso: la validación (SPEC-0002/0003)
solo corre plantillas de nuclei por servicio y, además, su `confirmed`
**sobreafirma** (marca confirmado un match por versión) y **descarta la severidad**.

El operador quiere lo que haría a mano con `curl` contra varias rutas: encontrar la
ruta expuesta, ver qué filtra, y quedarse con la **evidencia reproducible y
redactada** que vuelve el reporte creíble.

## Contexto
- `/api/validate` ([validation.py](../../src/api/routers/validation.py)) ya exige
  **scope estricto** (403 fuera de alcance) y el pipeline es **no destructivo** por
  diseño (`validator.py` docstring; `-etags dos,intrusive,fuzz,brute-force`).
- `Validator` es una **interfaz pluggable** (ABC,
  [validator.py:88](../../src/inter/validator.py#L88)); hoy solo `NucleiValidator`.
  Encaja añadir un segundo backend sin tocar el existente.
- `redact_snippet` ([validator.py:54](../../src/inter/validator.py#L54)) ya trunca y
  enmascara secretos: la evidencia se adjunta redactada, nunca en claro ni en logs.
- `ValidationResult` ([schemas.py:95](../../src/api/schemas.py#L95)) hoy no expone
  **ubicación** (la URL está enterrada en `evidence`), ni **clase**, ni **severidad**.
- `NucleiValidator._map` ya tiene a mano `info.name`, `info.severity`, `info.tags`,
  `matched-at` (la URL), `extracted-results`; solo usa una parte.

## Decisiones
- **Nuevo backend `SensitiveRouteValidator`** (en `src/inter/exposure.py`),
  implementa la interfaz `Validator`. Para cada servicio **HTTP/HTTPS en scope**:
  1. Deriva la base del objetivo (host + puerto del hallazgo).
  2. Hace **GET benignos** (no destructivo: solo GET, sin seguir redirecciones a
     otros hosts, timeout corto, nº de rutas acotado) a una **lista curada de rutas
     sensibles** versionada con OptiVeil (`.git/config`, `.env`, `backup.*`,
     `config.json`, `server-status`, `actuator`, `robots.txt`, listados de
     directorio, etc.).
  3. Sobre cada respuesta `200` con cuerpo, corre el **matcher de datos sensibles**.
  - Por qué una lista curada y no un crawler: cubre lo común, es bounded y legítimo
    (forced browsing no destructivo, como gobuster/ffuf en modo seguro). Enumerar las
    rutas **propias** de la app (crawling) es más grande → posible SPEC-0008.
- **Matcher de datos sensibles** (`src/inter/sensitive_data.py`): detecta **RUT
  chileno válido por módulo 11**, correos, tokens/secretos (reusando el patrón de
  `redact_snippet`) y firmas de exposición (listado de directorio, `KEY=VALOR` de un
  `.env`). Si hay match → `vuln_class = "exposición de datos sensibles"`. Por qué
  validar el dígito verificador del RUT: evita falsos positivos de números sueltos.
- **Enriquecer `ValidationResult`** con `name`, `severity` (normalizada
  info/low/medium/high/critical; desconocida → `"unknown"`), `location` (la URL/ruta
  exacta) y `vuln_class`. Por qué: es lo que convierte el resultado en un reporte
  (**dónde** y **qué**), no una etiqueta.
- **Reclasificar `status` con honestidad** (aplica a ambos backends): `confirmed`
  solo cuando hubo **contenido observado** (PII/secreto hallado, o `extracted-results`
  de nuclei); `version`/`tech` y **CVE-por-versión sin contenido** → `likely`. Por
  qué: que `confirmed` signifique "lo vi en la respuesta", como tu `curl`. Límite
  honesto documentado: la separación perfecta exigiría introspección de plantilla.
- **El endpoint corre ambos backends y fusiona** por hallazgo (nuclei + rutas
  expuestas). Invariantes intactos: no destructivo, scope estricto, evidencia
  redactada y fuera de artefactos versionados y del `audit.log`. Motor evolutivo y BD
  no se tocan.
- **Frontend:** por hallazgo, mostrar `vuln_class`, `location`, `severity` y
  evidencia; **ordenar por severidad** (lo crítico primero).

## Criterios de aceptación
1. Dado un objetivo HTTP en scope cuyo GET a una ruta de la lista devuelve `200` con
   un **RUT válido**, el resultado incluye: `status = confirmed`,
   `vuln_class = "exposición de datos sensibles"`, `location` = esa ruta/URL, y
   `evidence` con el RUT **redactado** (enmascarado, nunca en claro). *(Fetcher HTTP
   mockeado; no se toca la red en los tests.)*
2. Un RUT con **dígito verificador inválido** no dispara el detector (no falso
   positivo); un `.env` con `CLAVE=valor` sí dispara (firma de exposición).
3. Rutas que devuelven `404`/vacío → no generan hallazgo (no ruido).
4. `ValidationResult` expone `name`, `severity` (normalizada; desconocida →
   `"unknown"`) y `location` para los matches de nuclei; un match por versión/`tech`
   o `cve` sin contenido → `likely`; un match con contenido observado → `confirmed`.
5. El probe es **solo GET** y **no sigue redirecciones fuera del host** en scope
   (test: un redirect a otro host no se persigue).
6. Fuera de scope → 403 **antes** de cualquier GET; backend/fetcher ausente o error →
   degrada a `not_tested` (no 500). *(no-regresión de SPEC-0002/0003.)*
7. `pytest -ra` verde.

## Alcance
- **API:** `src/api/schemas.py` (`ValidationResult` + `name`/`severity`/`location`/
  `vuln_class`), `src/api/routers/validation.py` (correr y fusionar ambos backends).
- **IA/validación:** `src/inter/exposure.py` (nuevo backend `SensitiveRouteValidator`
  + lista curada de rutas), `src/inter/sensitive_data.py` (nuevo: matchers RUT/correo/
  secreto/firmas), `src/inter/validator.py` (`_map`: severity/location/class +
  reclasificación).
- **Frontend:** `frontend/src/components/IntelligenceResults.jsx` (render + orden por
  severidad).
- **Dependencia:** cliente HTTP para los GET. Decidir en el plan entre `httpx` (hoy
  solo dep de test) añadido a `src/requirements.txt`, o `urllib` de la stdlib. El
  fetcher es **inyectable** para testear sin red (patrón del `runner` de nuclei).
- **Fuera de alcance por tamaño** (recon válido en este proyecto, pero en otra
  tarea): **crawling** de las rutas propias de la app (enumerarlas siguiendo
  enlaces) → posible **SPEC-0008**. El motor evolutivo y la BD tampoco se tocan aquí.
- **Fuera de alcance por principio** (van a un proyecto ofensivo aparte, NO a
  OptiVeil): **explotar** de verdad la vulnerabilidad, y construir **herramientas que
  atacan** (weaponización). En concreto: nada que no sea GET, sin autenticar ni forzar
  credenciales, sin modificar/borrar estado, sin DoS. OptiVeil **encuentra y reporta
  con evidencia**; no ataca.

## Verificación
`pytest -ra` → **162 passed** (sin red: fetcher HTTP y runner de nuclei inyectados).
Tests nuevos:
- `tests/test_sensitive_data.py`: RUT módulo 11 (válido/inválido), `find_sensitive`
  (RUT/correo/`.env`/listado/secreto), y `mask_pii_in_text` (no filtra RUT ni correo).
- `tests/test_exposure.py`:
  - ruta con RUT → `confirmed` + `vuln_class` + `location` + evidencia **redactada**
    (criterio 1); RUT con DV inválido no dispara (criterio 2); `404`/vacío → sin
    hallazgo (criterio 3); `302` no se trata como hallazgo y solo se consulta el host
    objetivo (criterio 5); hallazgo no-HTTP se omite; error de fetcher no rompe
    (criterio 6).
  - reclasificación nuclei: CVE sin contenido → `likely`; contenido observado →
    `confirmed`; PII en contenido → `exposición de datos sensibles`; severidad
    desconocida → `"unknown"` (criterio 4).
  - `/api/validate` fusiona ambos backends; **scope bloquea con 403 antes de tocar
    cualquier backend/GET** (criterio 6).

Frontend: `npm run build` OK. Render del "Veredicto de exposición" (clase, ubicación,
severidad, evidencia; orden por severidad) verificable al levantar la app.

Dependencia: se usó `urllib` (stdlib), sin añadir dependencia de runtime; el fetcher
es inyectable.

## Preguntas abiertas (resueltas 2026-10-28)
1. **Patrones de datos sensibles iniciales:** RUT (módulo 11), correo, tokens/secretos
   y firmas de `.env`/listado de directorio. (Teléfono/tarjetas: posible ampliación
   futura, no en esta spec.)
2. **Estados:** se **reutiliza** `confirmed`/`likely` (expuesto+PII → `confirmed`;
   expuesto sin PII clara → `likely`). Sin estado `exposed` nuevo.
3. **Lista curada:** ~30-50 rutas de alto valor, versionada como dato.

## Enlaces
- Nace de la duda sobre SPEC-0002/0003 (el `confirmed` sobreafirmaba) y del objetivo
  de reportar rutas expuestas con evidencia.
- Posible continuación: SPEC-0008 (crawling de rutas propias de la app).
