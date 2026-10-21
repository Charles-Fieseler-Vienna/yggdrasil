---
nodeTypeId: node_ygg_evidence
nodeInstanceId: 01a15dd3-882d-7172-aedd-5302a47f524d
status: done
priority: normal
dateCreated: 2026-10-12
dateModified: 2026-10-12
confidence: low
completedDate: 2026-10-12
outcome: failed
legacy_ref: TREE 2.1
projects:
  - "[[control-decomposition]]"
  - "[[cosyne-2027-abstract]]"
---

## Purpose

Test whether learned nonlinear lifts of the kymograph (Koopman) beat linear dynamics.

## Method

MLP lifts and fixed EDMD dictionaries against linear ridge, leave-one-animal-out on 5 animals, forward runs only and
all states. Code: `Cosyne_2027@0164258:src/dynamics/koopman.py`.

## Results

- Forward runs: ridge h5 .844 / h15 .332, against .830 / .321 for the best MLP lift. EDMD dictionaries fail the same
  way, and the train−test gap grows with capacity.
- All states: lifts edge out ridge (MLP h10 +0.035) by learning an implicit state switch, but never beat the
  forward-specialised linear model on forward frames.
- Across FWD→REV transitions every model scores −0.03 at h5.

## Conclusion

Learned Koopman lifts do not improve posture forecasts over linear models; their only gain comes from implicitly
switching between states, which the modulated model does explicitly.

## Caveats

- 5-animal exploration subset; an oracle-switched linear baseline and a within-animal benchmark were never run.
- An earlier "decoder bottleneck" was a training bug (one Adam step per epoch).
