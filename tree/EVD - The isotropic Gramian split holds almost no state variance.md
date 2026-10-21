---
nodeTypeId: node_ygg_evidence
nodeInstanceId: 01a15dd3-8274-71a3-af6f-583160c49611
status: done
priority: normal
dateCreated: 2026-10-12
dateModified: 2026-10-12
confidence: low
completedDate: 2026-10-12
outcome: succeeded
legacy_ref: TREE 1.4
projects:
  - "[[control-decomposition]]"
---

## Purpose

Find out why the observable / unobservable split looked uninformative.

## Method

Compare the isotropic Gramian W (energy per unit norm in standardized delay coordinates) with a whitened Gramian
Σ^{1/2} W Σ^{1/2} (energy per unit data variance): the state variance held by the top-k subspace, and how well the
complement still predicts mid-body curvature y3. Then rerun the locomotion / navigation / silent split with the
whitened metric.

## Results

- Isotropic: the top-k subspace held 0.2–0.5 % of the state variance, and the "unobservable" complement still predicted
  y3 at R² 0.99.
- Whitened: the y3 top-k subspace holds 21 % of the state variance and the complement predicts ≤ 0.09.
- Whitened split on 5 animals: variance 5.5 / 2.4 / 92.1 %, k_loc / k_nav = 2 / 1, navigation bootstrap 37°, anterior
  enrichment −0.88 (p = 1).

## Conclusion

The isotropic Gramian ranks directions by norm rather than by information, so the split it gives is not an information
split. Whitening by the state covariance fixes this. The whitened parts are uncorrelated, not necessarily
independent.

## Caveats

- 5-animal exploration subset only; the whitened split was never rerun on 36 animals, and its navigation stability on
  the 5 animals (37°) was worse than the bar.
- The Cosyne_2027 notebook default is whitened; the CLI default stays isotropic
  (`observability.gramian_metric`).
- Decision log: `Cosyne_2027@0164258:docs/decision_log.md`, entries of 2026-10-12.
