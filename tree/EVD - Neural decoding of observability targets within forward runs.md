---
nodeTypeId: node_ygg_evidence
nodeInstanceId: 01a15dd3-82ff-7abd-93e8-787c94ff525f
status: done
priority: normal
dateCreated: 2026-10-11
dateModified: 2026-10-11
confidence: medium
completedDate: 2026-10-11
outcome: succeeded
legacy_ref: TREE 1.11
projects:
  - "[[control-decomposition]]"
---

## Purpose

Test whether the targets of the observability split are neurally encoded within forward runs.

## Method

Within-animal linear decoding from neurons with nested block cross-validation, forward runs only. Partial decoding
after removing the global FWD/REV manifold, with Benjamini–Hochberg correction across animals. Positive controls as in
`Cosyne_2027@0164258:scripts/diag_positive_controls.py`.

## Results

- Neurally silent within forward runs: speed y1, steering y2, the navigation subspace z_nav (≈ 0 or negative on 36
  animals), the inferred control inputs u, and head-complement PCs (0/25).
- Decodes (10 animals): raw y3 0.38, anterior curvature c05 0.77 and c20 0.76. c20 survives removal of the global
  manifold: partial 0.52, in 10/10 animals after correction.

## Conclusion

Within forward runs, neurons carry anterior body curvature beyond the global FWD/REV state, but not speed, steering or
the navigation subspace. The observability targets of the original plan have no neural readout at this resolution.

## Caveats

- Curvature decoding on 10 animals; z_nav from the isotropic Gramian.
- Linear decoders, which are blind to some nonlinear signals (TREE 3.12).
- Nuclear GCaMP at 3.5 Hz.
- Sources: `Cosyne_2027@0164258:WEEKEND_REPORT.md` Task 0, `Cosyne_2027@0164258:handoffs/HANDOFF_NEURAL_ADDS.md`.
