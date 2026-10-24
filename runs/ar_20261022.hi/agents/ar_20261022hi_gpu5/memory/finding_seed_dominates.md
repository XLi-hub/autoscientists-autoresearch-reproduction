---
name: seed-dominates
description: Seed choice, not run-to-run timing, dominates residual val_bpb at fixed steps; 3 same-code pairs observed
type: finding
---

Three same-code seed pairs now exist across teams (n=3, pooled sigma 0.002767, 2-sigma band 0.00553):
- exp_adam_beta2_hi: 1.093839 / 1.098235, |delta| 0.004396
- exp_warmdown_070:  1.093748 / 1.097886, |delta| 0.004138
- exp_activation_silu (mine, 2026-10-22): 1.092775 (seed42) / 1.095855 (seed43), |delta| 0.003080

Evidence that seed, not timing, is the residual: all three pairs had identical step counts and tokens
(725/725, 719/718), and my two seeds diverge ~0.01-0.03 nats in TRAIN loss within the first few hundred steps.

Operational consequence: a 1-seed improvement below 0.0055 is a coin flip. My seed42 leg of SiLU^2 was
-0.001262 (would have been a KEEP); seed43 was +0.001818 worse. ALWAYS run the second seed before promotion.
