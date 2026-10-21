---
nodeTypeId: node_ygg_evidence
nodeInstanceId: 01a15dd3-81f9-7d5e-b525-3379c7e27272
status: done
priority: normal
dateCreated: 2026-10-11
dateModified: 2026-10-11
confidence: low
completedDate: 2026-10-11
outcome: ambiguous
legacy_ref: TREE 1.3
projects:
  - "[[control-decomposition]]"
---

## Purpose

Test the pre-registered bars of the observability split on the full cohort.

## Method

Linear dynamics (iDMD, γ 0.85 / d 30 / λ 10, nd 5, chosen by leave-animals-out CV) on a standardized, delay-embedded
state of 12 eigenworm PCs and 24 Hilbert PCs, forward runs only. Isotropic output Gramians for speed y1 and steering y2
(heading rate and path curvature, in the body frame) give k = 3/3/3 locomotion / navigation / silent dimensions.
Stability is the bootstrap median angle of the navigation subspace across animals (bar: 30°); anterior enrichment tests
whether it loads on the anterior body.

## Results

36 animals:
- speed map C1: segment-block R² +0.51, leave-animals-out +0.35; steering map C2: +0.61, leave-animals-out +0.43;
- navigation bootstrap median angle **32.5°** against the 30° bar;
- anterior enrichment −0.002, p = 0.52.

Anterior enrichment flips sign with the dynamics selection: nd 16 fits are enriched (+0.07, p = 0.0005) but less stable
(38–49°). rSLDS forward segments in place of annotated ones give worse maps (C1 0.33, C2 0.53) and stability (37°).

## Conclusion

On the full cohort the navigation subspace narrowly misses its stability bar and is not anteriorly enriched, so the
observability split did not deliver a stable, interpretable navigation subspace. The miss is narrow and depends on the
dynamics selection.

## Caveats

- Isotropic Gramian only, which does not split information (TREE 1.4). The whitened version was never run on 36
  animals.
- Stability-gated model selection was recommended but never implemented (TREE 1.2): the strict 1-SE choice on the
  full grid is unstable (max|λ| 1.008).
- The observability-era `results/` were lost on 2026-10-14; only the numbers in the Cosyne_2027 documents survive.
  The pipeline is cached and deterministic, so they can be regenerated.
