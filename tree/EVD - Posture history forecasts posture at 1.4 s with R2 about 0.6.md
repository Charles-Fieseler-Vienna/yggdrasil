---
nodeTypeId: node_ygg_evidence
nodeInstanceId: 01a15dd3-869b-785a-ad25-3442b92de2be
status: done
priority: normal
dateCreated: 2026-10-16
dateModified: 2026-10-16
confidence: high
completedDate: 2026-10-16
outcome: succeeded
legacy_ref: "TREE 2.6, 3.6"
projects:
  - "[[control-decomposition]]"
  - "[[cosyne-2027-abstract]]"
---

## Purpose

Measure how well posture predicts its own future, and how much history is needed (Fig 1e).

## Method

Linear-history and modulated-model forecasts at h5 / h15 (1.4 s / 4.3 s), single animal and pooled; short histories of
one to six frames. Code: `Cosyne_2027@0164258:scripts/bench_single_ladder.py`,
`Cosyne_2027@0164258:scripts/diag_short_history.py`.

## Results

- Single animal, h5: linear history 0.614; two frames 0.531.
- Pooled 36 animals: the self-modulated model reaches h5 .68 and h15 .22.
- Reversal-vs-rest at the current frame: one posture frame 0.63 balanced accuracy, two frames 0.88. The second frame
  carries phase velocity, which separates forward from reverse rotation.

## Conclusion

Posture over the next ~1.4 s is largely predictable from its own recent history, and two frames already capture most
of what a 6-frame linear history achieves. Predictability falls to about a fifth of the variance at 4.3 s.

## Caveats

- Dev / test split 8 / 28; numbers on the 28 test animals.
- Forecast error concentrates around state changes (TREE 2.5).
