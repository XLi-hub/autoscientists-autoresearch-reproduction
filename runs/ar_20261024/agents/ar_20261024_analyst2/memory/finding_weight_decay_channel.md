---
name: finding_weight_decay_channel
description: WEIGHT_DECAY is the only never-varied constant and the only first-order gq lever; it also de-confounds the MATRIX_LR bracket because Muon decay is lr*wd*p
type: finding
---

2026-10-24 cycle 4, champion exp_tput_batch_2e17 (1.088286, 956 steps, 41.94M params,
20.97M 6N-FLOP-core, MLP_EXPANSION=2, MATRIX_LR 0.04).

**Mechanism.** `muon_step_fused` (train.py:349-353) applies
`p -= lr*g + lr*wd*p*mask`, `mask = (g*p) >= 0`. So Muon weight decay is (a) sign-masked
(cautious: only on coordinates where the gradient already points inward) and (b) scaled by
lr. `get_weight_decay(progress) = WEIGHT_DECAY*(1-progress)` and the LR multiplier is 1.0
for the first 50% of the run (WARMUP 0.0, WARMDOWN 0.5), so effective shrink is
0.04*0.2 = 0.8%/step at progress 0, mean ~0.4%/step over the flat half. That is a
first-order term in the update, unlike the beta2 horizons (20->100 steps = 2->10% of the
run) which measured null in BOTH optimizer groups (AdamW 0.37 sigma, Muon 0.18 sigma).

**Coupling that matters.** Both MATRIX_LR arms are LR+WD by construction: halving
MATRIX_LR 0.04->0.02 also halves effective decay. matrix_lr_lo landed -0.001303
(KEEP-UNCONFIRMED, seed 43 in flight) and matrix_lr_hi +0.003688 (0.64 sigma). A WD-only
change at fixed LR is the only attributable de-confounder for the decay channel.

**Dedup facts for reuse.** WEIGHT_DECAY appears 0 times in logs/experiments.jsonl as a
varied constant, in no result file, and had no row in knowledge/unqueued_axes.md before
this cycle. The value 0.2 is the pristine-upstream seed. The bracket filed is
{0.1, 0.4} around the implicit midpoint 0.2 (Step 3.4 cold-axis bracket), post 55aa397c.

**Capacities re-priced at MLP=2 (base 41.94M / 20.97M FLOP-core / 956 steps).** ar80_w640
57.67M (+37.5%) / FLOP-core +50% / ~650 steps; depth12_w512 58.72M (+40.0%)/+40%/~690;
mlp_exp_5 is 2->5 (NOT 3->5) = 54.53M (+30.0%)/+60%/~620; ve_density_2 33.55M (-20.0%),
FLOP-core unchanged -> ~956 steps; depth6_w512 33.55M (-20.0%), -20% FLOP-core -> ~1190.
Step cost at this base is only ~+0.0003 per -10% steps, so none of these is disqualified by
losing steps. Every stale queue number in the run came from mixing an MLP=3 or 2**19 base,
not from a modelling error.

**Noise update.** exp_cal_champion_seed43 = 1.090998 vs 1.088286 (|delta| 0.002712) is the
4th same-code pair and the first at the 956-step champion; pooled per-run sigma ~0.0027,
2-sigma ~0.0055. The gate is now anchored at the current base.
