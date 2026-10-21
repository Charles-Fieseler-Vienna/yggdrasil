---
nodeTypeId: node_ygg_evidence
nodeInstanceId: 01a15dd3-8a8e-7179-b05b-31e78d0b0b28
status: done
priority: normal
dateCreated: 2026-10-18
dateModified: 2026-10-18
confidence: medium
completedDate: 2026-10-18
outcome: succeeded
legacy_ref: "TREE 3.5, 3.13"
projects:
  - "[[control-decomposition]]"
  - "[[cosyne-2027-abstract]]"
---

## Purpose

Find out when neural activity reflects a new behavioural state, and whether faster readouts help.

## Method

Decode the state from neurons at lags around each onset; try temporal differences, causal inverse filters
(deconvolution) and high-pass filtering against raw lag-0 features; simulate a perfect but late regime readout.

## Results

- The state decodes from neurons at the frame, but the readout dips just after an onset (reverse balanced accuracy 0.42
  at +1..+2 frames). Read 0.9 s later, it recovers sooner.
- Differences, inverse filters and high-pass filtering never beat raw lag-0 features.
- The neural information about a new state arrives ~2–4 frames (0.6–1.2 s) after the switch.
- A perfect but 3-frame-late regime readout is already at or below the linear posture model across transitions.

## Conclusion

Neurons report a behavioural state change about a second late, and no readout trick recovers it sooner, so the
post-transition gain is a late report rather than anticipation.

## Caveats

- Consistent with GCaMP indicator delay, but the analysis does not separate indicator delay from neural delay.
- Nuclear GCaMP at 3.5 Hz.
