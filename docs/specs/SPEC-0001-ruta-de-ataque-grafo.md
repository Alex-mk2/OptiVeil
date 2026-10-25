# SPEC-0001 — Ruta de ataque como grafo priorizado

- **Tipo:** feature
- **Estado:** Implementada
- **Fecha:** 2026-10-25
- **Rama:** perf/offensive-ai-speed
- **Autor:** Alex-mk2

## Problema
`generate_attack_path()` ya prioriza bien los hallazgos (CVEs reales del NVD +
CVSS + MITRE ATT&CK + detección/mitigación), pero devuelve una **lista lineal**
de pasos (1→2→3→4→5) y el frontend la pinta como línea de tiempo. Un ataque real
no es lineal: tiene **precondiciones y bifurcaciones** (puntos de entrada
alternativos; movimiento lateral que depende de un foothold previo). La vista
lineal oculta esa estructura.

## Contexto
- Lógica en [src/inter/IA_offensive.py](../../src/inter/IA_offensive.py);
  esquema `AttackRoadmap`/`AttackStep` en
  [src/api/schemas.py](../../src/api/schemas.py); render en
  [frontend/src/components/AttackRoadmap.jsx](../../frontend/src/components/AttackRoadmap.jsx),
  consumido desde `IntelligenceResults.jsx:183`.
- El frontend ya usa `reactflow` en `NetworkMap.jsx` → hay patrón para dibujar un grafo.
- Restricción de la rama actual (`perf/offensive-ai-speed`): no romper la
  optimización de rendimiento (una sola generación del LLM, máx. 5 pasos).
- La salida del LLM es input no confiable (regla zero-trust del repo): puede traer
  ciclos o referencias a pasos inexistentes.

## Decisiones
- **Modelar la ruta como DAG con un campo aditivo `depends_on` por paso.**
  Por qué: es el cambio mínimo que captura dependencias sin reescribir la
  priorización. Alternativa descartada: una estructura de grafo nueva y separada
  → más invasiva y rompería compatibilidad.
- **Saneo determinista "solo-hacia-atrás": una dependencia es válida solo si
  apunta a un id existente y menor que el del propio paso.** Por qué: elimina de
  una sola regla autoreferencias, referencias colgantes, forward-refs y cualquier
  ciclo (todas las aristas van de menor a mayor id → DAG garantizado), y encaja
  con la semántica "ataca primero lo de mayor prioridad". Alternativa descartada:
  detección de ciclos por DFS → más código y menos predecible.
- **`depends_on` opcional con default `[]`.** Por qué: compatibilidad hacia atrás;
  el render lineal actual sigue funcionando como fallback.
- **Alcance de esta iteración: backend + frontend completo** (reescribir el render
  a reactflow). Decidido con el usuario.

## Criterios de aceptación
1. `POST /api/strategy/live` devuelve, por cada paso, `depends_on: [ids]` (`[]` = entrada).
2. Integridad del grafo: todo id en `depends_on` existe y es menor que el del paso;
   entradas inválidas del LLM se sanean sin romper la respuesta (acíclico garantizado).
3. Compatibilidad hacia atrás: la respuesta conserva `steps` con todos los campos
   actuales; `depends_on` es opcional.
4. El prompt pide las dependencias sin perder el límite de 5 pasos ni la generación única.
5. Los fallbacks devuelven forma válida (`depends_on=[]`).

## Alcance
- **IA:** `src/inter/IA_offensive.py` — prompt + función `sanitize_dag`.
- **API:** `src/api/schemas.py` — `AttackStep.depends_on: List[int]` + coerción.
- **Frontend:** `AttackRoadmap.jsx` — render DAG con reactflow (fallback lineal).
- **Fuera:** motor evolutivo (minimización no aplica), BD (sin migración).

## Verificación
Implementada el 2026-10-25. Suite completa verde: `pytest -ra` → **108 passed**
(37 en `tests/test_offensive.py`). Tests añadidos:
- `sanitize_dag`: ids colgantes, autoreferencia, ciclos (1↔2), forward-refs,
  deduplicación, dependencias válidas conservadas.
- `AttackStep`: default `[]` y coerción de `depends_on` (None/int/lista/no-numérico).
- `generate_attack_path` sanea `depends_on` (dependencia colgante descartada,
  válida conservada).

Cambios: `src/api/schemas.py` (campo + coerción), `src/inter/IA_offensive.py`
(`sanitize_dag`, prompt regla 7, aplicación tras el roadmap),
`frontend/src/components/AttackRoadmap.jsx` (render DAG con reactflow + fallback
lineal). Frontend fuera de pytest (verificación visual pendiente al levantar el dev server).

## Enlaces
- Flujo: skill `sdd_feature`.
- Rendimiento previo de la IA ofensiva: commit `f1bceb4`.
