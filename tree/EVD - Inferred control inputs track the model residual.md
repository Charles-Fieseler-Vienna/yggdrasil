---
nodeTypeId: node_ygg_evidence
nodeInstanceId: 01a15dd3-83c4-781b-b070-eca3f82474f1
status: done
priority: normal
dateCreated: 2026-10-12
dateModified: 2026-10-12
confidence: medium
completedDate: 2026-10-12
outcome: failed
legacy_ref: TREE 1.10
projects:
  - "[[control-decomposition]]"
---

## Purpose

Infer control inputs to the linear posture dynamics (Stage 4) and test whether they look like sparse control events.

## Method

unDMDc with AIC-selected inputs, held-out input dimension q, comparison of the inputs with the no-input model
residual, and neural decoding of the inputs. Code: `Cosyne_2027@0164258:src/dynamics/undmdc.py`.

## Results

- The AIC-best inputs are dense small corrections: active-frame fraction 0.74, mean |u| 0.008 against a state std of 1.
- ‖u‖ against the no-input residual: r = 0.94.
- Held-out q saturates at 8 (q = 12 at M = 36). Bu avoids the speed and locomotion directions; navigation is at chance.
- Oracle inputs help up to h15 and hurt at h30, because the joint A is unstable.
- u decodes from neurons at chance (0/60).
- 29 % of input spikes coincide with fast head-tip casts (chance ~1 %).

## Conclusion

The inferred inputs absorb the model residual rather than marking sparse control events, and they are neurally
invisible, so input inference as framed does not identify control signals.

## Caveats

- The head-cast coincidence follows from the inputs absorbing the residual, so it is not independent support for
  control events.
- Linear joint model; the observability-era results were lost on 2026-10-14.
