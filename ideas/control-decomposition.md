---
type: project
title: Control decomposition
created: 2026-10-20
roots:
  - "[[QUE - Does observability split posture dynamics into interpretable subspaces]]"
---

## Summary

Can worm posture be decomposed into a predictable plant plus control channels (navigation, speed, head exploration)
that have distinct timescales and body subspaces, are stable across animals, and beat plain regression readouts; and
does at least one channel show a neural signal? The programme is set out in `Cosyne_2027@0164258:research/FRAMEWORK.md`;
the current feasibility sprint in `Cosyne_2027@0164258:research/NEXT_STEPS.md`.

The Cosyne_2027 project (2026-10-09 → 2026-10-19) was its first phase. Its detailed tree is
[[@Cosyne_2027 research tree]].

## Findings

- The observability split as first run gives no stable navigation subspace, but it narrowly missed and used a flawed
  Gramian ([[CLM - Observability decomposition gives no stable navigation subspace]], [[CLM - Isotropic observability Gramians do not split state information]]); the whitened rerun is open ([[QUE - Does the whitened observability split hold on the full cohort]]).
- Steering is neurally silent within forward runs, while anterior curvature is encoded beyond the global state
  ([[CLM - Steering is neurally silent within forward runs]], [[CLM - Anterior body curvature is neurally encoded beyond the global state]]).
- Head bending is driven continuously at the head ([[CLM - Head bending is continuously driven]]).
- Posture dynamics are a modulated mixture of a few linear regimes, the best plant so far ([[CLM - Posture dynamics are a modulated mixture of a few linear regimes]]).
