---
nodeTypeId: node_ygg_dataset
nodeInstanceId: 01a15dd3-80b5-7d96-8378-48d0f6abc178
status: done
priority: normal
dateCreated: 2026-10-09
dateModified: 2026-10-09
completedDate: 2026-10-09
location: /lisc/data/scratch/neurobiology/zimmer/fieseler/paper/nwb/no_images/exported_data_/
n_animals: 36
n_recordings: 36
projects:
  - "[[control-decomposition]]"
  - "[[cosyne-2027-abstract]]"
---

## Description

Whole-brain imaging of freely moving *C. elegans*, exported as NWB without images: 36 recordings of 4.0–8.0 min,
84–134 neurons each (4169 in total, 1212 identified), 53,869 frames at 0.288 s per frame (h5 = 1.4 s, h15 = 4.3 s,
h30 = 8.6 s), and 579 direct FWD→REV transitions. REV→FWD happens almost only through a turn (7 direct).

The neural signal is ΔR/R50 = (R − R50)/R50, where R is the GCaMP / red reference ratio and R50 its median
(`neural_dfof` in the Cosyne_2027 code).

For the Cosyne 2027 paper, 8 development animals (aid % 5 == 0) chose every hyperparameter and all reported numbers
come from the other 28.

## Provenance

Read live from the cluster with h5py (`h5py.File(path, "r", locking=False)`); pynwb hangs on these files. Code:
`Cosyne_2027@0164258:src/data/loading.py`. Dataset numbers: `Cosyne_2027@0164258:paper/results_snapshot/dataset_numbers/`.

Known fixes needed before use (TREE 0):
- 10 of 36 recordings are mirrored; a per-animal chirality puts steering in the body frame.
- `angular_velocity` is sign-flipped in 12 of 36 exports.
- `ZIM2165_Gcamp7b_worm5-2022-12-10` has all-NaN Hilbert features.
- `2023-11-30_13-58_wt_worm3_FM` is unpredictable from posture (h5 linear R² −0.33).
