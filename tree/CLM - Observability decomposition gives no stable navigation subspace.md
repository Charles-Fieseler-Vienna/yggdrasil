---
nodeTypeId: node_ygg_claim
nodeInstanceId: 01a15dd3-8236-7b9e-be08-7bae3f0f70a9
status: open
priority: normal
dateCreated: 2026-10-21T11:38:24+02:00
dateModified: 2026-10-21T11:38:24+02:00
confidence: low
projects:
  - "[[control-decomposition]]"
---

## Claim

The observability split of linear posture dynamics, as run in the Cosyne_2027 project, does not give a navigation
subspace that is stable across animals or loads on the anterior body.

## Rationale

The navigation subspace missed its stability bar (32.5° against 30°) and showed no anterior enrichment on 36 animals
([[EVD - Navigation subspace misses its stability bar]]).

## Scope

36-animal cohort, isotropic Gramian, linear iDMD dynamics. Not tested with the whitened Gramian, stability-gated
selection, or the modulated model as the plant. The feasibility sprint reruns it, so this claim is open and may be
superseded.
