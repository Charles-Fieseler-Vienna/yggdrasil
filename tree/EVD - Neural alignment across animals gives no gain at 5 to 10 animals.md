---
nodeTypeId: node_ygg_evidence
nodeInstanceId: 01a15dd3-8938-79ec-aca8-ac047c54ff5a
status: done
priority: normal
dateCreated: 2026-10-14
dateModified: 2026-10-14
confidence: low
completedDate: 2026-10-14
outcome: failed
legacy_ref: TREE 3.11
projects:
  - "[[control-decomposition]]"
  - "[[cosyne-2027-abstract]]"
---

## Purpose

Test whether pooling neurons across animals improves neural models.

## Method

PPCA imputation of identified neurons, and ID-free alignment by optimal transport plus generalized Procrustes, with
zero-shot transfer and pooled training on 5–10 animals. Code: `Cosyne_2027@0164258:src/neural/align.py`.

## Results

- PPCA imputation mostly carries the shared FWD/REV drive.
- ID-free alignment transfers FWD/REV zero-shot in part (held-out label R² 0.30 against 0.43 within animal), gives no
  gain for an animal that already has its own fit, and is flat in the number of training animals.

## Conclusion

Aligning neurons across animals, with or without identities, recovers the shared FWD/REV state but does not improve
an animal's own neural model at 5–10 animals.

## Caveats

- Only 5–10 animals; posture models needed 5–20 pooled animals to pay off, so this may be under-scaled.
- Linear alignment; the SSL alignment project tests nonlinear alternatives. Notes:
  `Cosyne_2027@0164258:results/impute_ids/NOTES.md`.
