# exp_warmup_0p1 — LR warmup WARMUP_RATIO 0.0 -> 0.1

- **Agent:** ar_20261022hi_gpu4
- **Team:** gradient-quality (H-gradient-quality)
- **Outcome:** DISCARD
- **val_bpb:** 1.223462
- **Champion at evaluation:** 1.195701 (baseline_shared)
- **Delta (minimize):** +0.027761 (worse)
- **Direction / axis / value:** increase / warmup_ratio / 0.1
- **Hardware adaptation:** DEVICE_BATCH_SIZE 128 -> 64 (upstream 128 OOMs on 32 GB RTX 4080S). TOTAL_BATCH_SIZE unchanged at 2**19 (grad_accum 4). This matches the shared baseline's adaptation exactly, so the comparison is valid.
- **Runtime:** training_seconds 300.3, total_seconds 370.0, num_steps 190, total_tokens 99.6M, peak_vram 22805.5 MB, MFU 7.59%
- **Command:** `CUDA_VISIBLE_DEVICES=1 /root/autodl-tmp/envs/ar/bin/python3 train.py` (uv venv creation is blocked by shared-cache lock contention; pre-provisioned env has identical torch 2.9.1+cu128)

## Experiment Description

Add a linear LR warmup over the first 10% of the time budget (`WARMUP_RATIO = 0.1`). Hypothesis H-gradient-quality predicted that reducing early update noise / improving early update direction would KEEP. The warmup ramps lrm from 0 to 1.0 over the first ~30 s, then follows the unchanged schedule (constant to 50%, half-budget warmdown).

## Training Dynamics

| progress | warmup loss | baseline loss |
|---|---|---|
| ~20% (step ~47) | 5.550 | 5.050 |
| ~50% (step ~100) | 4.248 | 3.963 |
| ~80% (step ~154) | 3.586 | 3.481 |
| ~90% (step ~172) | 3.503 | 3.419 |
| final (step ~190) | 3.452 | 3.365 |

- **Loss still decreasing at end** (3.586 @80% -> 3.452 final, -3.7%): the run is undertrained; step-increasing changes are productive.
- **No early plateau**: loss falls smoothly through the whole budget.
- **Steps:** 190 vs 193 baseline (-1.6%, run-to-run timing noise; same 300 s budget and same batch size).
- **Interpretation:** the warmup interval spends ~10% of the fixed time budget at lrm < 1.0 and the run never recovers the ~0.086-nat training-loss gap. In a fixed-wall-clock benchmark the cost of warmup is not amortized, because the schedule (and the budget) end when training ends. This is consistent with the system's throughput-centric view and counts as evidence against warmup under a 300 s budget, though the effect is confounded with the shortened effective peak-LR horizon.
- **Magnitude:** the gap (+0.027761 val_bpb) is ~18x the conservative noise-floor default (0.0015) and ~2.3% relative, far outside seed noise. Not a near-miss.
