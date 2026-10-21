---
nodeTypeId: node_ygg_evidence
nodeInstanceId: 01a15dd3-8617-7604-aa77-f190eb95e8fd
status: done
priority: normal
dateCreated: 2026-10-16
dateModified: 2026-10-16
confidence: medium
completedDate: 2026-10-16
outcome: succeeded
legacy_ref: TREE 3.7
projects:
  - "[[control-decomposition]]"
  - "[[cosyne-2027-abstract]]"
---

## Purpose

Measure how much neural variance posture and behaviour explain, linearly and nonlinearly (Fig 1b, c).

## Method

Linear and MLP maps from a 6-frame posture history to ΔR/R50, and a linear map from 20 frames of behaviour, held out by
animal. Code: `Cosyne_2027@0164258:src/neural/resid.py`; snapshot `paper/results_snapshot/neural_resid/`.

## Results

- 6-frame posture history (Fig 1b): linear ≈ −0.02, MLP 15 % (median over animals).
- 20 frames of behaviour, linear, 36 animals: 0.32 of raw ΔR/R50 variance (CI 0.25–0.36), mostly PC1 (R² 0.85, 41 % of
  the variance). Future behaviour adds nothing.
- Strongly behavioural neuron classes: AVA, AVE, RIM, AVB, BAG and AQR. URX, RIS, ALA, URAD, AUA and IL1 are ≈ 0.

## Conclusion

Posture history predicts neural activity only through a nonlinear map (15 % against ≈ 0 linearly). Most of the
behaviour-explained neural variance is the global PC1 state.

## Caveats

- Behaviour features that include speed and state are linearly predictive (0.32), so "only nonlinearly" holds for
  posture, not for behaviour in general.
- Frontend leak: the posture PCA and standardization are pooled, not fit per animal or per fold.
