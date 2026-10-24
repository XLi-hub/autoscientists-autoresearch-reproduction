---
name: weight-decay-schedule
description: Why the WEIGHT_DECAY coefficient bracket was flat — the schedule zeroes the term at progress 0.5
type: feedback
---

# WEIGHT_DECAY is scheduled to zero before the eval point (factual finding)

`champion/train.py`:
- line 533: `get_weight_decay(progress) = WEIGHT_DECAY * (1 - progress)`
- `get_lr_multiplier` is 1.0 only while `progress < WARMDOWN_RATIO == 0.5`, then anneals to FINAL_LR_FRAC=0.
- line 352-353: `mask = (g*p) >= 0; p.sub_(lr*g + lr*wd*p*mask)` — sign-masked, applied only to Muon 2D
  matrix groups (line 261); every AdamW group passes `weight_decay=0.0` (lines 251-255).

Consequence: the applied shrink `lr*wd*p` is **zero by the halfway point of the run**, while val_bpb is
evaluated on end-of-run weights. So the coefficient has no path to the final metric except through the
first-half trajectory, which the final eval largely forgets.

Measured (2 seeds per arm, same GPU, seed-matched to champion 1.088286):
| arm | 2-seed mean | delta | loss@80% | final loss |
|---|---|---|---|---|
| 0.1 | 1.088044 | -0.000242 | 3.129/3.139 | 3.051/3.059 |
| 0.4 | 1.090118 | +0.001832 | 3.160/3.160 | 3.063/3.063 |

Doubling WD costs ~0.024 loss at the 80% mark and converges to within 0.012 at the end; val_bpb never
moves outside noise. Generalizable rule: before spending a slot on a regularizer's coefficient, check
whether its schedule zeroes the term before the evaluation point.

Also: the "first-order term" reasoning in the original proposal was correct about per-step magnitude
(0.8%/step at progress 0) but magnitude is not the binding constraint — the timing is.
