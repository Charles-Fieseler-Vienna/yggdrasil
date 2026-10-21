---
nodeTypeId: node_ygg_evidence
nodeInstanceId: 01a15dd3-8be8-7d9a-be0c-894d0bf9740c
status: done
priority: normal
dateCreated: 2026-10-15
dateModified: 2026-10-15
confidence: low
completedDate: 2026-10-15
outcome: ambiguous
legacy_ref: TREE 3.8
projects:
  - "[[control-decomposition]]"
  - "[[cosyne-2027-abstract]]"
---

## Purpose

Test whether neurons predict the hazard of a forward-to-reverse switch.

## Method

Hazard models on stacked neural features against a time-shifted null, at leads of up to 4.3 s; carriers identified by
neuron. Code: `Cosyne_2027@0164258:src/neural/transition.py`; report
`Cosyne_2027@0164258:results/transition_predict/REPORT.md`.

## Results

- +0.026 AUC [+0.007, +0.043] at a 4.3 s lead; ~0 at ≤ 1.4 s. Concatenating all neural features overfits.
- Positive in 4 of 5 recording months; no single group confirms it.
- Carriers: SIAV, RMDV, RID and URAD, which behaviour barely explains. No identified neuron leads the switch; pre-onset
  RIS / RIB track the visible deceleration.
- Removing drift increased the signal.

## Conclusion

There is a small, early neural signal for upcoming reversals, but it is not established: it came out of a screen of
~25 variants × 8 leads and no subgroup confirms it.

## Caveats

- Needs a pre-registered confirmation on held-out data before it counts.
- Worth retrying with drift handled explicitly and a single pre-registered feature set.
