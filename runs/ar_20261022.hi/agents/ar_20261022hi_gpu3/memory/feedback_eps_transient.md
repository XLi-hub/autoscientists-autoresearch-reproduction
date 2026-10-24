---
name: eps_transient
description: AdamW eps 1e-10->1e-6 is a TIE on final val_bpb but a measurable EARLY transient - judge eps on the early curve
type: feedback
---

Measured 2026-10-22 by ar_20261022hi_gpu3 (exp_adam_eps_hi), 718 steps, val_bpb 1.098069
(+0.004032 = 1.34 sigma vs champion, i.e. a tie on the final metric).

Corrected dynamics (matched steps, eps_hi vs champion-code reference):
  step 50: 5.312 vs 5.162 | 100: 4.648 vs 4.257 | 142: 4.127 vs 3.827 |
  200: 3.707 vs 3.607 | 300: 3.513 vs 3.473 | 360: 3.439 vs 3.409 | final ~3.078 vs 3.058

Mechanism: early in training the AdamW second moment v is small, so sqrt(v) is comparable to 1e-6 and
the eps term damps the update; once v accumulates, sqrt(v) >> eps and the damping disappears. So the
'rare-token undamped unit update' story is right in kind but is a TRANSIENT that the 300 s budget erases.

Two lessons: (1) evaluate eps (and any conditioning constant) on the early loss curve, because the final
val_bpb hides the transient; (2) the 1e-8 control arm is only 100x from 1e-10 and is predicted sub-band -
do not spend a slot on it.
