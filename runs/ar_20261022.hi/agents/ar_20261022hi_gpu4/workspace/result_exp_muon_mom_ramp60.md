# exp_muon_mom_ramp60 — Muon momentum ramp 300 -> 60 steps

- **Agent:** ar_20261022hi_gpu4
- **Team:** gradient-quality (H-gradient-quality)
- **Outcome:** DISCARD (near-miss band)
- **val_bpb:** 1.174107
- **Champion at evaluation:** 1.170054 (exp_batch_2e18, TOTAL_BATCH_SIZE=2**18)
- **Delta (minimize):** +0.004053 (worse) = 2.7x the conservative 0.0015 noise floor
- **Direction / axis / value:** decrease / muon_momentum_ramp / 60
- **Config:** champion + `frac = min(step/60, 1)` in `get_muon_momentum()`; momentum endpoint 0.95 unchanged. DEPTH 8, DEVICE_BATCH_SIZE 64, TOTAL_BATCH_SIZE 2**18.
- **Runtime:** training_seconds 300.8, total_seconds 361.7, num_steps 368, total_tokens 96.5M, peak_vram 22805.5 MB, MFU 7.54%
- **Command:** `CUDA_VISIBLE_DEVICES=1 /root/autodl-tmp/envs/ar/bin/python3 train.py`

## Experiment Description

The upstream Muon momentum ramp `frac = min(step/300, 1)` interpolates 0.85 -> 0.95 over 300 steps, calibrated for long runs. With the halved TOTAL_BATCH_SIZE the 300 s budget yields ~373 steps, so the old ramp reaches 0.95 only at step 300 (80% of the run). This experiment shortens the ramp to 60 steps so momentum reaches the designed 0.95 by step 60 (16% of the run).

## Training Dynamics

| progress | ramp60 loss | champion loss |
|---|---|---|
| ~20% (step ~82) | 4.479 | 4.440 |
| ~50% (step ~189) | 3.673 | 3.676 |
| ~80% (step ~296) | 3.413 | 3.401 |
| ~90% (step ~331) | 3.342 | 3.339 |
| final (step ~368) | 3.290 | 3.273 |

- **Loss still decreasing at end** (3.413 @80% -> 3.290 final, -3.6%): still undertrained.
- **No early plateau.**
- **Steps:** 368 vs 373 (-1.3%, run-to-run timing variance at the same 300 s budget).
- **Interpretation:** the shorter ramp is neutral-to-slightly-negative. The 50%-progress losses are essentially identical (3.673 vs 3.676) and the gap opens only in the final 20%, so the signal is weak. Delta (0.004053) is above the conservative 0.0015 noise floor but well below the champion's own 0.0256 KEEP delta, and the team has no measured seed sigma yet. Treat as a *near-miss*, not a confirmed refutation: the momentum-ramp axis is not closed by a single seed.
