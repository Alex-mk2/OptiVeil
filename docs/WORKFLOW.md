# Flujo de trabajo de OptiVeil

Punto de entrada único para entender cómo se trabaja en este repo y, sobre todo,
**dónde recurrir cuando necesites recuperar información**. Pensado para ti (y para
cualquier yo-del-futuro que abra el proyecto tras meses sin tocarlo).

## El ciclo

```
Petición ambigua
      │
      ▼
 disambiguate   → dilucida con PROGRESS.md + graphify + specs; pregunta solo si hace falta
      │
      ├──► sdd_feature   (funcionalidad nueva)
      └──► sdd_bug_fix    (algo roto)
                 │
                 ▼
   Fase 1  crea docs/specs/SPEC-NNNN   (problema, contexto, decisiones: durable)
   Fase 2  plan de cambios
   Fase 3-4  implementación (+ `graphify update .`)
   Fase 5  verificación (pytest) y marca la spec "Implementada"
                 │
                 ▼
   project_memory actualiza .claude/PROGRESS.md   (estado de hoy; enlaza la spec)
```

Las skills son una **guía, no un peaje**: en un cambio trivial, una spec de dos
líneas —o saltársela— está bien. El dueño del repo manda sobre el proceso.

## Dónde vive cada cosa (las 3 capas de contexto)

| Si buscas... | Mira en... | Naturaleza |
|---|---|---|
| Cómo está construido OptiVeil (arquitectura, comandos, reglas) | [CLAUDE.md](../CLAUDE.md) | Estable |
| Dónde está una función / cómo se conecta con otra | `graphify query "..."`, `graphify path "A" "B"` | Consultable |
| Qué se decidió en una feature/bug y **por qué** | [docs/specs/](specs/) (índice en [README](specs/README.md)) | Durable, por ítem |
| En qué estábamos trabajando últimamente | [.claude/PROGRESS.md](../.claude/PROGRESS.md) | Volátil |

Regla práctica: la **spec** responde "¿por qué hicimos esto así?"; la **bitácora**
responde "¿en qué iba?"; el **grafo** responde "¿dónde está esto en el código?".

## Cómo arrancar una tarea

1. Si la petición es clara, entra directo en `sdd_feature` o `sdd_bug_fix`.
2. Si es vaga ("mejora la IA", "algo va lento"), entra en `disambiguate` primero.
3. Toda decisión no trivial deja rastro en una `SPEC-NNNN`; el estado del día, en
   la bitácora.

## Las skills (en `.claude/skills/`)

- **disambiguate** — puerta de entrada para peticiones ambiguas.
- **sdd_feature** — flujo SDD para funcionalidad nueva.
- **sdd_bug_fix** — flujo SDD para arreglar bugs (empieza por un test que falla).
- **project_memory** — mantiene la bitácora `.claude/PROGRESS.md`.
- **graphify** — grafo de conocimiento del código.

## Specs

Registro numerado y correlativo (`SPEC-NNNN`, único para features y bugfixes).
Plantilla en [docs/specs/_TEMPLATE.md](specs/_TEMPLATE.md); índice con estado en
[docs/specs/README.md](specs/README.md).
