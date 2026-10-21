---
nodeTypeId: node_ygg_evidence
nodeInstanceId: 01a15dd3-8c76-7c47-9276-21d7e7803c69
status: done
priority: normal
dateCreated: 2026-10-14
dateModified: 2026-10-14
confidence: low
completedDate: 2026-10-14
outcome: promising-out-of-scope
legacy_ref: TREE 3.9
projects:
  - "[[control-decomposition]]"
  - "[[cosyne-2027-abstract]]"
---

## Purpose

Test whether identified neurons around a reversal predict the next forward bout's speed.

## Method

Leave-one-animal-out regression from identified neurons around each reversal to the next bout's speed, against a rich
behaviour history, on 31 recordings. Sources: `Cosyne_2027@0164258:handoffs/HANDOFF_OVERNIGHT.md` item 7,
`handoffs/HANDOFF_SHORT_HISTORY_RESID.md` test c.

## Results

- LOAO R² +0.04..+0.07 beyond behaviour history.
- Carriers: a ventral/dorsal head asymmetry (SIAV, RIV +; SIAD, SMDD −) plus O2/CO2 sensory neurons (BAG +, AQR −).
- About 80 % of the composite's gain disappears after residualization.

## Conclusion

Identified neurons carry a small signal about the next forward bout's speed, but most of it is a record of past
behaviour, so it is a lead rather than a result.

## Caveats

- 31 recordings; never confirmed.
- Worth retrying with residualization built into the test and a pre-registered neuron set.
