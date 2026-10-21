---
nodeTypeId: node_ygg_claim
nodeInstanceId: 01a15dd3-8406-742c-a14c-6bad2c86c4ba
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

Control inputs inferred for linear posture dynamics (unDMDc) are dense small corrections that track the model
residual, not sparse control events.

## Rationale

The inputs are active in 74 % of frames and correlate with the no-input residual at r = 0.94; they do not decode from
neurons ([[EVD - Inferred control inputs track the model residual]]).

## Scope

Linear dynamics with unDMDc on 36 animals. A better plant (e.g. the modulated model) might leave a residual with more
structure.
