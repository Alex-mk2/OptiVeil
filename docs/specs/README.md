# Specs de OptiVeil

Registro durable de decisiones por feature/bugfix (estilo ADR + spec). Cada
entrada captura **problema, contexto y decisiones con su porqué**, para que no se
pierdan con el tiempo. Lo gestionan las skills `sdd_feature` y `sdd_bug_fix`
(su Fase 1 crea la spec; la Fase 5 la marca `Implementada`).

- **Numeración:** `SPEC-NNNN`, correlativa y única para features y bugfixes. El
  siguiente número es el mayor existente + 1.
- **Plantilla:** [_TEMPLATE.md](_TEMPLATE.md).
- **Estado volátil** (en qué vamos hoy) → `.claude/PROGRESS.md`, no aquí.

| ID | Título | Tipo | Estado | Fecha |
|----|--------|------|--------|-------|
| [SPEC-0001](SPEC-0001-ruta-de-ataque-grafo.md) | Ruta de ataque como grafo priorizado | feature | Implementada | 2026-10-25 |
