---
name: seed-noise-floor
description: First empirical same-code seed pair — seed choice dominates 0.0002-0.0004 deltas
type: feedback
---

Measured 2026-10-22 on the champion code (DEPTH=8, TOTAL_BATCH_SIZE=2**17, 729 steps, 300 s):
exp_adam_beta2_hi (ADAM_BETAS beta2=0.99) run with only torch.manual_seed differing.

- seed 42 -> val_bpb 1.093839
- seed 43 -> val_bpb 1.098235
- spread 0.004396; implied 1-sigma ~ 0.003108 (n=1, weak)
- Same-seed reference: champion (seed 42) 1.094037 vs this code (seed 42) 1.093839 = 0.000198,
  so same-seed / run-to-run reproducibility is ~2e-4.

Consequence: any single-seed delta below ~0.004 is not evidence. The conservative 0.003 band is if
anything too tight. This pair is registered in main knowledge/noise_floor_data.md (created this
cycle) and team knowledge/noise_floor.md. Independently, exp_warmdown_070 (1.093748, +0.000289 vs
champion) showed the same pattern: seed-43 leg worse.
