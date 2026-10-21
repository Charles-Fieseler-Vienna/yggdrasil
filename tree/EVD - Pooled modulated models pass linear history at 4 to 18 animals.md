---
nodeTypeId: node_ygg_evidence
nodeInstanceId: 01a15dd3-8724-7162-9a60-88563ab48dfa
status: done
priority: normal
dateCreated: 2026-10-17
dateModified: 2026-10-17
confidence: medium
completedDate: 2026-10-17
outcome: succeeded
legacy_ref: "TREE 2.4, 2.6"
projects:
  - "[[control-decomposition]]"
  - "[[cosyne-2027-abstract]]"
---

## Purpose

Compare nonlinear and linear posture models fit to one animal or pooled across animals, and find the data scale at
which nonlinear models pay off (Fig 1e, i, j).

## Method

Single-animal ladder (2-D and 4-D modulated models against linear history), pooled 12-D modulated model, a shared GRU
baseline, and a scaling curve over the number of training animals. Code: `Cosyne_2027@0164258:scripts/bench_scaling.py`
→ `scripts/analyze_scaling.py`; `scripts/run_single_ladder.sh`.

## Results

- Single animal, h5: nonlinear K2/M1 0.364 and K4/M1 0.450 against 0.614 for linear history.
- Pooled over 36 animals: the 12-D modulated model beats linear history by +0.07–0.08 at 1.4–4.3 s. The true
  annotated states would add only ~0.03–0.06 more (oracle).
- Scaling: the pooled model passes linear history between 4 and 9 training animals at 1.4 s, and between 9 and 18 at
  4.3 s. Linear history does not improve with pooling.
- Shared GRU: h5 .559 against .68 for the self-modulated model.

## Conclusion

Nonlinear posture models lose to linear history when fit to one animal and win only when pooled across roughly 5–20
animals, so the data scale, not the model class, limits single-animal models.

## Caveats

- The 12-D model has one initialization; 2-D model seeds 1–4 are in `results/scaling_s1..4/` and not merged.
- Fits depend on the thread count (1 thread per process in production).
- Dev / test split 8 / 28.
