---
nodeTypeId: node_ygg_evidence
nodeInstanceId: 01a15dd3-8b13-7bd9-b035-f35d2eea1e58
status: done
priority: normal
dateCreated: 2026-10-15
dateModified: 2026-10-15
confidence: medium
completedDate: 2026-10-15
outcome: succeeded
legacy_ref: "TREE 3.7, 3.9, 3.10"
projects:
  - "[[control-decomposition]]"
  - "[[cosyne-2027-abstract]]"
---

## Purpose

Test whether neural signals that seem to predict upcoming behaviour survive removing what past behaviour explains.

## Method

Residualize neurons (and targets) on behaviour history, then retest regime identity, next-bout speed and within-run
wave frequency. Code: `Cosyne_2027@0164258:src/neural/resid.py`, `scripts/diag_setpoint_{decode,residual}.py`.

## Results

- Regime identity, next-bout and within-run signals in residualized neurons all turn out to be records of past
  behaviour.
- Within-run wave frequency: with run means removed, neurons give R² 0.075 (positive in 25 of 33 animals), but only
  concurrently, with no forecast gain, and ≈ 0 after residualizing on past frequency. The run set point drifts down over
  the recording (median correlation with time −0.72) and is not neurally predicted.
- Next-bout speed: about 80 % of the neural composite's gain disappears after residualization.

## Conclusion

Neural signals that look predictive of upcoming behaviour are mostly lagged records of past behaviour. Testing for
neural prediction needs residualization on behaviour history.

## Caveats

- Linear residualization; a nonlinear dependence on past behaviour could hide more.
- The remaining ~20 % of the next-bout signal is unexplained (see the open question on next-bout speed).
