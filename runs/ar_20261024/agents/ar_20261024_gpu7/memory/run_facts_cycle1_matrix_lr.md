---
name: matrix-lr-bracket-cycle1
description: First MATRIX_LR (Muon LR) bracket on the 956-step champion; both arms inside noise
type: findings
---

# MATRIX_LR bracket (cycle 1, 2026-10-24, GPU 1)

Base: champion exp_tput_batch_2e17, val_bpb 1.088286 (AR64/w512, DEPTH 8, MLP_EXPANSION 2,
TOTAL_BATCH 2**17, DEVICE_BATCH 64, compile max-autotune-no-cudagraphs). sigma = 0.002865
(2-sigma band 0.00573), n_pairs = 3, all measured on 1.19-era code.

| MATRIX_LR | val_bpb | delta vs champ | verdict |
|---|---|---|---|
| 0.02 | 1.086983 | -0.001303 | KEEP-UNCONFIRMED (inside noise, NOT promoted) |
| 0.04 | 1.088286 | 0 | champion midpoint |
| 0.08 | 1.091974 | +0.003688 | DISCARD (inside noise, axis open) |

- Both arms are LR+WD-confounded: muon_step_fused decays as lr*wd*p, so 0.08 doubles and 0.02 halves
  the effective per-step decay (0.8% -> 1.6% / 0.4% at progress 0).
- The full span of the bracket is 0.0064 bpb ≈ 1.1 sigma. The axis is noise-limited at this budget.
- Training dynamics: 952-956 steps, 124.9-125.3M tokens, peak VRAM 18.48 GB, final-20% loss drop
  1.11-1.64% of range -> still undertrained in both arms.
- Open follow-up: seed-43 repeat of MATRIX_LR=0.02 (the only candidate improvement, 0.45 sigma).
