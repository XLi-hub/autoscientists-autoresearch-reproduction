---
name: saturation-at-956-steps
description: The step/token channel is saturated at the 956-step champion; structure at fixed cost is the only live channel
type: finding
---

# Finding: the training budget saturates at the 956-step champion (2026-10-24)

Measured, not inferred:
- 2**19 -> 2**18: 193 -> 374 steps, val_bpb -0.0235 (KEEP).
- 2**18 -> 2**17: 374/487 -> 956 steps, -0.0437 (KEEP, champion 1.088286).
- 2**17 -> 2**16: ~1850 steps, -0.0027 (1.1 sigma) = FLAT.
- exp_cap_ar48_b2e17: 1348 steps AND 176.7M tokens (+41% both) in the same 300 s -> 1.088598, **+0.000312**.

So above ~950 steps, neither optimizer steps nor tokens buy anything. All five optimizer-geometry axes
(betas both groups, muon momentum, LR ratios, schedule shape) landed inside 0.45 sigma of the champion.

The only outside-noise effect measured after the champion landed is structural and cost-free:
`exp_cap_head_dim_64` = +0.007723 (2.70 sigma) at 0 FLOP change and +512 params.

Consequence for proposal writing: any arm that pays or earns steps is dead weight at this base. The productive
space is representational structure at fixed step count and fixed FLOPs (head geometry, value-embedding density,
depth/width lattice), plus the one first-order optimizer term never varied (WEIGHT_DECAY).

Noise: sigma 0.002503 (5 same-code pairs, the 5th seed-only/same-GPU); 2 sigma = 0.005007. A fine bracket below
0.006 cannot resolve anything here; that is why MATRIX_LR 0.02's -0.0013 "KEEP" evaporated on re-seed.
