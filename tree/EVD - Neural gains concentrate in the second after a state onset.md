---
nodeTypeId: node_ygg_evidence
nodeInstanceId: 01a15dd3-8a08-7a7d-be53-01129c91d5d2
status: done
priority: normal
dateCreated: 2026-10-18
dateModified: 2026-10-18
confidence: medium
completedDate: 2026-10-18
outcome: succeeded
legacy_ref: TREE 3.5
projects:
  - "[[control-decomposition]]"
  - "[[cosyne-2027-abstract]]"
---

## Purpose

Measure the neural contribution to posture forecasts around state onsets (Fig 2).

## Method

Pooled 12-D modulated models trained from scratch with and without neurons, scored 0–1 s after each state onset at h5;
per-animal comparisons against posture history; decoding the state from neurons at lags around the onset. Code:
`Cosyne_2027@0164258:scripts/diag_state_decode.py`, `scripts/bench_neural_scratch.py`.

## Results

- Pooled, R² 0–1 s after onset at h5: self-modulated 0.00–0.03; + neurons up to the frame before each predicted frame
  0.22; + neurons 2 frames (0.6 s) after each predicted frame (acausal) 0.44–0.47; true state 0.63.
- Per animal against posture history: +0.17 with neurons up to the frame, +0.38 late; within states −0.03 late and
  −0.10 up to the frame.

## Conclusion

Neurons improve posture forecasts mainly in the first second after a state transition, where posture-only models fail.
Within states they do not help.

## Caveats

- 3 initializations per row (5 for the self-modulated model); figure rows average over seeds.
- 25 of 28 test animals have enough post-onset windows.
- The hull-label rSLDS was fit on all frames (affects the oracle row).
