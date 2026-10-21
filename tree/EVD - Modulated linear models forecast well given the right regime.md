---
nodeTypeId: node_ygg_evidence
nodeInstanceId: 01a15dd3-87a8-73d7-812b-a333c9dc476f
status: done
priority: normal
dateCreated: 2026-10-13
dateModified: 2026-10-13
confidence: medium
completedDate: 2026-10-13
outcome: succeeded
legacy_ref: "TREE 1.9, 2.2, 2.3, 2.5"
projects:
  - "[[control-decomposition]]"
  - "[[cosyne-2027-abstract]]"
---

## Purpose

Find a posture model that captures the switching between behavioural regimes.

## Method

Per-state linear fits on behavioural rSLDS states; a modulated low-dimensional model z+ = (A0 + Σ m_i A_i) z + b with
m a soft mixture of learned atoms (dLDS-like), first initialised from the convex hull of a behavioural rSLDS and later
learned from scratch; an oracle ladder over how much regime information the model is given; self-modulation by an
MLP on the latent history. Code: `Cosyne_2027@0164258:src/dynamics/modkoop.py`.

## Results

- Forward runs split by wave frequency (0.10 / 0.14 / 0.19 Hz); per-state fits on the dwelling states give h15 R² +0.20
  / +0.35, against −0.07 for the pooled forward model.
- The elbow is at r = 3 atoms in 9 of 9 fits: fast forward (0.25 Hz), slow forward (0.06–0.15 Hz, which carries the
  turns), and reverse.
- Oracle ladder (K5, h15): no modulation 0.18, self-modulation 0.24, true regime at t 0.30, true regime at every step
  0.62.
- Self-modulation beats no modulation (h15 +0.05–0.14 at K3, 5/5 folds); on 36 animals it is the best posture model
  (h5 .68, h15 .22).
- Forecast error concentrates on reversals and turns, and within 5 frames of a state change (36–42 % of the error in
  27 % of frames).

## Conclusion

Posture dynamics are well described by a few linear regimes mixed by a learned modulation. The model forecasts well
when given the right regime sequence, so most of its remaining error is not knowing when the regime changes.

## Caveats

- The hull labels are a smoothing posterior, so they are an oracle (a causal filtered version gives the same result).
- `rslds.prepare_pooled` z-scored the PCA modes and silently broke one pipeline path until fixed.
