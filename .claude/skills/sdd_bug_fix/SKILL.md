---
name: sdd_bug_fix
description: >-
  Flujo Spec-Driven Development para ARREGLAR un bug en OptiVeil:
  reproducir con un test que falle → diagnosticar → arreglar mínimo →
  verificar → blindar. Úsala siempre que el usuario reporte que algo no
  funciona, da error, devuelve un resultado incorrecto o se comporta distinto
  de lo esperado, aunque no diga "bug". Dispara con "falla", "da error",
  "no funciona", "devuelve mal", "se rompe", "excepción", "el test X falla",
  "debería hacer Y pero hace Z". Para añadir funcionalidad NUEVA usa
  `sdd_feature` en su lugar.
---

# SDD: Arreglar un bug en OptiVeil

La trampa clásica de un bug fix es "arreglar" sin reproducir: parcheas un
síntoma, no sabes si era la causa, y nada impide que vuelva. Este flujo empieza
por un **test que falle** que capture el bug, y solo entonces arregla. Así el
arreglo queda demostrado y blindado contra regresiones.

Registra el bug como una spec durable: calcula el siguiente `SPEC-NNNN` mirando
`docs/specs/` (mayor + 1; numeración única con las features), copia
`docs/specs/_TEMPLATE.md` a `docs/specs/SPEC-NNNN-<slug>.md` con `Tipo: bugfix` y
anota el síntoma y cómo se reproduce en **Problema**. La **causa raíz** irá en
**Decisiones** cuando la tengas (Fase 2).

Contexto obligatorio: [CLAUDE.md](../../../CLAUDE.md) y
[.claude/context.md](../../context.md). Reglas que condicionan un fix:

- **NSGA-II = minimización.** Si el bug está en el motor evolutivo, el arreglo
  mantiene la lógica como minimización. Nunca introduzcas maximización.
- **Dos estilos de import.** La API usa `src.inter.xxx`; el engine usa
  `inter.xxx` vía `sys.path.append`. Si el bug es un ImportError, comprueba por
  cuál de los dos caminos entra (los tests cargan ambas raíces vía `conftest.py`).
- **Zero-trust.** Muchos bugs vienen de confiar en input/datos de Scapy sin
  validar. Sospecha de eso primero.

## Fase 0 — Rama

Una rama por bug. Nunca arregles sobre `main` ni reutilices la rama de otra
tarea. Antes de escribir el test de la Fase 1, nace una rama desde la base
**actualizada**:

```bash
git switch main && git pull --ff-only
git switch -c fix/<slug-corto>        # mismo slug que el SPEC-NNNN
```

Si el bug vive en código que **aún no está en `main`** (otra rama sin mergear),
basa la rama en esa rama en vez de `main`, y déjalo anotado en la spec
(`Rama base:`). Así cada fix es aislado, revisable y revertible por separado.

## Fase 1 — Reproducir (test que falla primero)

Antes de tocar código fuente, escribe un test que **reproduzca el bug y falle**.
Esto es lo que convierte el arreglo en permanente: el test es el candado contra
la regresión.

- Reutiliza los patrones existentes: SQLite en memoria (ya por `conftest.py`),
  `TestClient` para endpoints, mocks para Scapy y para el LLM. Nunca red real ni
  llamadas reales al LLM.
- El test debe fallar por la razón del bug, no por un error de montaje. Córrelo y
  confirma que falla como esperas:

```bash
pytest tests/test_x.py::test_reproduce_el_bug -x
```

Si no logras reproducirlo con un test, para y acuerda con el usuario los pasos
exactos de reproducción antes de seguir. Un bug que no sabes reproducir no lo
sabes arreglar.

## Fase 2 — Diagnóstico

Localiza el mecanismo, no adivines. Usa el grafo antes que grep/lectura a ciegas:

```bash
graphify query "dónde se procesa <cosa>?"
graphify path "<A>" "<B>"        # cómo se conecta A con B
graphify explain "<concepto>"
```

Lee en crudo solo las líneas que el grafo (o una lectura previa) ya localizó.
Formula la causa raíz en una frase: "X ocurre porque Y". Si no puedes, sigue
investigando — no arregles sobre una hipótesis sin confirmar. Cuando la tengas,
anótala en **Decisiones** de la spec `SPEC-NNNN` que abriste al empezar.

## Fase 3 — Arreglo mínimo

- El cambio más pequeño que corrige la causa raíz. Resiste la tentación de
  refactorizar de paso; si ves deuda cercana, anótala, no la mezcles.
- Respeta el estilo del módulo que tocas (nombres, comentarios, idioma).
- Si el fix cambia un modelo de BD, genera la revisión Alembic correspondiente.

## Fase 4 — Verificación

- El test de la Fase 1 ahora **pasa**.
- La suite completa sigue verde (no has roto nada):

```bash
pytest -ra
```

- Tras modificar código: `graphify update .` para mantener el grafo al día.

## Fase 5 — Blindaje

Repaso final antes de dar por cerrado:

- ¿El arreglo tiene implicaciones de autorización? Si toca una operación sobre un
  target, confirma que sigue pasando por `enforce_scope`.
- ¿El bug podía explotarse con input malicioso? Endurece la validación, no solo
  el caso concreto reportado.
- Sin secretos en código ni en el test.

El bug está cerrado cuando: hay un test que lo reproducía y ahora pasa,
`pytest -ra` está verde, y entiendes y puedes explicar la causa raíz (no solo que
"ya no falla"). Reporta la causa raíz al usuario, no solo el hecho de que está
arreglado.

Al cerrar, marca la spec `docs/specs/SPEC-NNNN-*.md` como `Estado: Implementada`,
rellena **Verificación** (el test de regresión y comandos) y actualiza su fila en
`docs/specs/README.md`.
