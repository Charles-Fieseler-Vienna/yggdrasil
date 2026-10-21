---
nodeTypeId: node_ygg_evidence
nodeInstanceId: 01a15dd3-88ae-7839-a80d-35520eb09c56
status: done
priority: normal
dateCreated: 2026-10-17
dateModified: 2026-10-17
confidence: high
completedDate: 2026-10-17
outcome: succeeded
legacy_ref: "TREE 3.1, 3.3, 3.4, 3.12, 3.14"
projects:
  - "[[control-decomposition]]"
  - "[[cosyne-2027-abstract]]"
---

## Purpose

Measure how much whole-brain activity improves posture forecasts, read at the forecast time and as an ongoing input
(Fig 1g, h).

## Method

Gains over a time-shifted neural null for linear-history and modulated models, single animal and pooled. "Forecast":
neurons up to the forecast time t. "Driven": neurons up to t+h−1 for predicted frame t+h. Neural lags are causal, with
group ridge and in-fold PCA. A simulated-neuron positive control and robustness splits by recording date.

## Results

- Forecast, single animal: gain over the shift null ≤ 0.01 at every horizon, within states and across transitions.
- Forecast, pooled 36 animals: −.014 at h5 and +.009 at h15 over the self-modulated model; neurons explain ~0 of its
  residual.
- Driven: the 2-D modulated model gains 0.014 → 0.054, growing with horizon; linear history gains ≤ 0.011. No neural
  gain lifts a single-animal model above the pooled posture-only model.
- Positive control: the nonlinear causal test detects a 4 s pre-reversal ramp neuron at SNR ~0.3 (observed per-neuron
  SNR median 77); linear forecast and residual decoders are blind to it.
- Robustness: no recording-date group shows a causal within-state gain; no relation to neuron count or SNR proxies.
- Early screens showed +0.12 (forward, h15) because they used acausal neural lags (−2..+2), which decode rather than
  forecast since GCaMP lags behaviour, and one shared ridge penalty for ~155 posture and ~600 neural columns. With
  causal lags the gain is −0.03.

## Conclusion

Within behavioural states, whole-brain activity adds essentially nothing to posture forecasts read at the forecast
time, and at most ~0.05 as an ongoing input. The nonlinear test is sensitive enough that this is not a power
problem.

## Caveats

- Nuclear GCaMP at 3.5 Hz.
- 2023–24 recordings show larger gains, confounded with recording length.
- A linear null alone would not be evidence of absence; the conclusion rests on the nonlinear tests.
