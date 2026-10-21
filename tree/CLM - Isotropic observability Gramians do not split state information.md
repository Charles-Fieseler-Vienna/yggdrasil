---
nodeTypeId: node_ygg_claim
nodeInstanceId: 01a15dd3-82b6-7201-87f5-26ee991c66a2
status: done
priority: normal
dateCreated: 2026-10-21T11:38:25+02:00
dateModified: 2026-10-21T11:38:25+02:00
confidence: medium
completedDate: 2026-10-21
projects:
  - "[[control-decomposition]]"
---

## Claim

An observability Gramian computed per unit norm in standardized delay coordinates picks directions that hold almost
none of the state variance, so the observable / unobservable split it gives is not an information split. Whitening by
the state covariance (Σ^{1/2} W Σ^{1/2}) gives a split that is.

## Rationale

The isotropic top-k subspace held 0.2–0.5 % of the variance while its complement still predicted curvature at R² 0.99;
whitened, the top-k holds 21 % and the complement predicts ≤ 0.09 ([[EVD - The isotropic Gramian split holds almost no state variance]]).

## Scope

Linear, delay-embedded posture dynamics; shown on 5 animals. The argument is general to Gramians in standardized
delay coordinates.
