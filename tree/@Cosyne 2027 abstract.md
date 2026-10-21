---
nodeTypeId: node_ygg_source
nodeInstanceId: 01a15dd3-817c-762a-823e-ea48899f4602
status: done
priority: normal
dateCreated: 2026-10-19
dateModified: 2026-10-19
completedDate: 2026-10-19
figures:
  - Cosyne_2027@438457f:paper/abstract/cosyne2027.pdf
projects:
  - "[[control-decomposition]]"
  - "[[cosyne-2027-abstract]]"
---

## Description

"What would a generative model of worm behavior need from the brain?", submitted to Cosyne 2027 at
`Cosyne_2027@438457f` (merged into `main` as `eabf5bd`). Two figures, about 12 panels. Every panel's source is in the
docstring of `Cosyne_2027@438457f:paper/make_figures.py` (partly stale; the code is right), audited against the result
files on 2026-10-18.

Caveats carried into the abstract: the posture PCA and standardization are pooled rather than fit per fold; the
hull-label rSLDS was fit on all frames (affects only the oracle and pretraining labels); the single-animal modulated
model in Fig 1 is the 2-D one, although development selection preferred 4-D.
