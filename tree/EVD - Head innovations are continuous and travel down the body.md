---
nodeTypeId: node_ygg_evidence
nodeInstanceId: 01a15dd3-8550-7c8b-b01f-1b975aaae17e
status: done
priority: normal
dateCreated: 2026-10-12
dateModified: 2026-10-12
confidence: medium
completedDate: 2026-10-12
outcome: succeeded
legacy_ref: "TREE 1.6, 1.7, 1.12, 1.13"
projects:
  - "[[control-decomposition]]"
---

## Purpose

Find out why head curvature is unpredictable and what drives it.

## Method

Curvature-probe forecasts (c05–c85) from data and from the held-out model; a phase-diffusion test with the
instantaneous head frequency; one-step head residuals ("innovations"): their propagation speed, their concentration in
time against an event-free surrogate, and their decorrelation time; the same forecasts on the 12 ms re-export.

## Results

- h15 (4.3 s) R², data / model: c05 0.09 / 0.12, c25 0.20 / 0.26, c55 0.42 / 0.46, y3 0.39 / 0.42 (36 animals). The
  anterior body alone predicts as well as the whole body; the held-out model tracks the data-only predictor.
- Instantaneous head frequency hurts prediction at every horizon (h15 circular R² 0.15 against 0.39 for persistence).
- Innovations travel down the body at 9.6–9.8 labels/s. The top 10 % of frames hold 48 % of the non-propagated head
  energy, against 47 % for an event-free surrogate. They decorrelate in ~130 ms. Two event families: slow anterior
  bends and fast tip wobbles.
- 12 ms sampling does not make the future more predictable: y3 0.97 / 0.88 / 0.69 at 48 ms against 0.97 / 0.91 / 0.73
  at 288 ms, at matched durations.
- The innovations are not visible in neural activity at 3.5 Hz with nuclear GCaMP.

## Conclusion

Head curvature is driven by continuous, fast inputs at the head that then travel down the body as the wave. It is not
drift in the wave's phase and not a sequence of sparse events, and finer behavioural sampling does not make it more
predictable.

## Caveats

- The cohort size of the innovation analysis is not recorded in TREE; sprint task S2 reruns it on the full cohort
  (`scripts/diag_highres_innovation.py --n 0`). Its results directory was lost on 2026-10-14.
- Neural invisibility may reflect the indicator's speed (~130 ms decorrelation against 3.5 Hz imaging) rather than
  absence of a neural signal.
