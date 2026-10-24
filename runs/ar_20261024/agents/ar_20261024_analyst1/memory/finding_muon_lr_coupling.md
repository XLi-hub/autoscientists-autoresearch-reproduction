---
name: muon-lr-coupling
description: Muon weight decay is scaled by MATRIX_LR, and matrix_lr is the only LR not width-scaled
type: project
---

Two code facts in `champion/train.py` that make MATRIX_LR a non-obvious knob (found cycle 3, discussion round):

1. **Weight decay is multiplied by the LR.** `muon_step_fused` (train.py:358) does
   `stacked_params.sub_(lr * g + lr * wd * stacked_params * mask)`. The decay term is `lr*wd*p`.
   With WEIGHT_DECAY=0.2 and WARMUP_RATIO=0, the champion shrinks each masked coordinate by
   `0.04*0.2 = 0.8%` per step at progress 0. Changing MATRIX_LR therefore changes effective weight
   decay proportionally: 0.02 -> 0.4%/step, 0.08 -> 1.6%/step. The cautious mask `(g*p)>=0`
   moderates but does not remove the coupling. Any MATRIX_LR arm is an LR+WD arm; to attribute a
   hi-arm DISCARD, hold `lr*wd` constant (MATRIX_LR=0.08 with WEIGHT_DECAY=0.1).
   The AdamW path has the same shape (`p.mul_(1 - lr_t * wd_t)`) but its lr is ~10x smaller.

2. **dmodel_lr_scale is not applied to matrix_lr.** train.py:248 computes
   `(model_dim/768)**-0.5` (1.2247 at width 512) and applies it to lm_head, embedding, VE and scalar
   groups only; `matrix_lr` is passed raw at train.py:505. So at width 512 the Muon:Adam LR ratio is
   ~18% below the 768-dim design ratio.

Param accounting at the champion (width 512, DEPTH 8, MLP_EXPANSION 2, vocab 8192, total 41.94M):
- wte 4.19M (10.0%), lm_head 4.19M (10.0%), VE tables 4x4.19M = 16.78M (40.0%), block matrices
  16.78M (40.0%). `estimate_flops` excludes wte+VE+scalars, so the 6N term counts 20.97M, of which
  the Muon group is 16.78M = 80.0%.
- This is why "40% of params" and "80% of FLOP-relevant params" are both correct for the Muon group.

Proposals filed: exp_gq_matrix_lr_lo (0.02) and _hi (0.08), post 552e2db3, gq queue v12.
