---
name: disambiguate
description: >-
  Dilucida una petición AMBIGUA o poco específica antes de ponerse a trabajar en
  OptiVeil. Úsala cuando no esté claro QUÉ se pide o DÓNDE actuar: peticiones
  vagas ("mejora la IA", "arregla el escaneo", "algo va lento", "optimiza esto"),
  un objetivo que podría tocar varios módulos, señales contradictorias, o cuando
  no se sabe si es feature o bug. Resuelve la ambigüedad con la evidencia del
  repo primero y, solo si hace falta, hace UNA pregunta concreta. Una vez claro,
  deriva a `sdd_feature` (funcionalidad nueva) o `sdd_bug_fix` (algo roto).
---

# Dilucidar una petición ambigua en OptiVeil

Actuar sobre la primera interpretación de una petición vaga es caro: se trabaja
sobre el módulo equivocado y se tira el esfuerzo. Pero preguntar por todo también
cansa. El objetivo de esta skill es el punto medio: **reducir la ambigüedad con
lo que ya sabemos del repo, y preguntar solo lo que de verdad no se puede inferir.**

## 1. Nombra la ambigüedad

Antes de nada, di en una frase qué es lo que no está claro. Suele ser una de estas:

- **Qué** se pide (el objetivo es difuso: "mejorar", "optimizar", "que sea mejor").
- **Dónde** actuar (podría ser el motor, la API, la IA, el frontend...).
- **Tipo**: ¿es una feature nueva o algo que ya existe y está roto?
- **Alcance**: ¿un arreglo puntual o un cambio estructural?

Hacer explícita la ambigüedad ya evita medio malentendido.

## 2. Resuélvela tú primero (evidencia barata antes de preguntar)

No traslades al usuario trabajo que puedes hacer con el contexto que ya existe:

- **`.claude/PROGRESS.md`** — ¿hay algo en curso con lo que esto conecte? Muchas
  peticiones vagas se refieren a lo último que se tocó.
- **`graphify query "<lo que dijo el usuario>"`** — ¿a qué símbolos/archivos
  reales podría referirse? Si solo hay un candidato plausible, la ambigüedad de
  "dónde" se disuelve sola.
- **`docs/specs/`** — ¿hay una spec relacionada que fije contexto o decisiones
  previas?

Después de esto, muchas veces ya puedes proponer una interpretación razonable.

## 3. Decide: proponer o preguntar

- **Si puedes inferir un default sensato**, no bloquees: enuncia la interpretación
  con la que vas a proceder y sigue ("Entiendo que te refieres a X en `engine.py`;
  voy por ahí; si era otra cosa, dímelo"). Es menos fricción que una pregunta.
- **Si siguen vivas varias interpretaciones de verdad distintas** (llevan a
  trabajo muy diferente), haz **una** pregunta concreta, con opciones mapeadas a
  los candidatos reales del repo — no una pregunta abierta. Ejemplo:
  "¿'mejorar la IA' es (a) acelerar la generación —ya vas en esa rama—,
  (b) mejorar la calidad del análisis, o (c) añadir una capacidad nueva?"

Evita los dos extremos: adivinar y equivocarte, o preguntar lo que podrías haber
deducido en 30 segundos con el grafo y la bitácora.

## 4. Deriva

Cuando la petición ya es nítida, sal de esta skill y entra en la que toca:

- Funcionalidad nueva o ampliación → **`sdd_feature`**.
- Algo que no funciona, da error o devuelve mal → **`sdd_bug_fix`**.

Esta skill es solo la puerta de entrada: su éxito es dejar la petición lo bastante
clara como para que el flujo SDD arranque sin dar bandazos.
