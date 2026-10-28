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
| [SPEC-0002](SPEC-0002-validacion-no-destructiva.md) | Validación no destructiva de explotabilidad | feature | Implementada | 2026-10-25 |
| [SPEC-0003](SPEC-0003-validador-nuclei-timeout.md) | El validador nuclei siempre degrada a not_tested | bugfix | Implementada | 2026-10-25 |
| [SPEC-0004](SPEC-0004-nmap-enforce-scope.md) | `/api/nmap` no pasa por enforce_scope ni audita | bugfix | Implementada | 2026-10-25 |
| [SPEC-0005](SPEC-0005-nmap-usa-nsga.md) | `/api/nmap` consume la config de NSGA-II (no presets -T) | feature | Implementada | 2026-10-25 |
