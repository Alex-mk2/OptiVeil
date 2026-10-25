---
name: project_memory
description: >-
  Mantiene el ESTADO DE TRABAJO de OptiVeil en una bitácora persistente
  (.claude/PROGRESS.md) para no tener que releer todo el repo cada sesión.
  Úsala al RETOMAR el trabajo ("¿dónde íbamos?", "retomemos", "sigue con lo de
  ayer", "ponte al día") para orientarte leyendo la bitácora en vez de escanear
  el código entero; y al CERRAR una tarea o tomar una decisión importante
  ("guarda el estado", "apunta esto", "actualiza el progreso") para dejar traza.
  No es para arquitectura estable (eso vive en CLAUDE.md) ni para estructura de
  código (eso lo da `graphify query`): es para el estado volátil del trabajo en
  curso.
---

# Memoria de trabajo de OptiVeil

El problema que resuelve: cada sesión nueva empieza en frío y se va el tiempo
(y el contexto) releyendo el repo para recordar en qué estábamos y por qué se
decidió algo. Esta skill mantiene un único archivo, `.claude/PROGRESS.md`, con el
estado volátil del proyecto, para orientarte leyendo **una página** en vez de
reconstruirlo todo.

Divide el trabajo entre tres fuentes — no las mezcles:

- **CLAUDE.md** → cómo está construido OptiVeil (arquitectura, comandos, reglas).
  Estable. Se carga sola.
- **`graphify query "..."`** → dónde está cada cosa en el código. Se regenera del
  código.
- **`.claude/PROGRESS.md`** (esta skill) → en qué estamos, qué decidimos y por
  qué, qué falta. Volátil, cambia cada sesión.

## Al retomar el trabajo

Cuando el usuario quiera continuar o preguntar dónde iban:

1. Lee `.claude/PROGRESS.md` **primero**. Si no existe, créalo con la plantilla
   de abajo y pregunta al usuario en qué está trabajando.
2. Para recordar la estructura del código, usa `graphify query`, no relecturas
   masivas. Lee archivos en crudo solo las líneas que la bitácora o el grafo ya
   señalaron.
3. Resume en una o dos frases el estado actual y propón el siguiente paso. No
   reconstruyas todo el historial en voz alta.

## Al avanzar o decidir

Actualiza `.claude/PROGRESS.md` en estos momentos (no en cada micro-paso):

- Terminas una tarea o un hito.
- Tomas una decisión no obvia (y por qué se eligió esa opción).
- Descubres una "trampa" del repo que costó tiempo entender.
- El usuario dice explícitamente "apunta/guarda esto".

Reglas para que la bitácora siga siendo útil y no un vertedero:

- **Concisa.** Una línea por entrada. Si necesitas párrafos, va en un doc aparte
  y la bitácora lo enlaza.
- **Fechas absolutas.** "el 2026-02-14", nunca "ayer" ni "la semana pasada".
- **Poda.** Cuando algo pendiente se completa o una decisión queda obsoleta,
  muévelo o bórralo. La bitácora refleja el presente, no un registro histórico.
- **Por qué, no solo qué.** Una decisión sin su motivo no sirve para el futuro.
- **No dupliques las specs.** Si una decisión está documentada a fondo en una
  spec (`docs/specs/SPEC-NNNN`), en la bitácora pon una línea que la enlace, no el
  razonamiento entero. La bitácora dice "en qué vamos"; la spec, "qué se decidió y
  por qué".

## Plantilla de `.claude/PROGRESS.md`

Si no existe, créalo así:

```markdown
# OptiVeil — Bitácora de trabajo

> Estado volátil del proyecto. Arquitectura estable → CLAUDE.md. Estructura de
> código → `graphify query`. Esta bitácora → en qué vamos y por qué.

## Estado actual
- Rama: <rama> — <qué se está haciendo en ella, en una frase>
- Tarea en curso: <descripción + en qué fase está>

## Decisiones
- AAAA-MM-DD — <decisión>. Por qué: <motivo>.

## Pendientes
- [ ] <próximo paso concreto>

## Trampas conocidas
- <algo no obvio del repo que conviene recordar>
```

Mantén las secciones; si una está vacía, déjala con un guion. El objetivo es que
una sesión nueva lea este archivo y en 30 segundos sepa dónde retomar.
