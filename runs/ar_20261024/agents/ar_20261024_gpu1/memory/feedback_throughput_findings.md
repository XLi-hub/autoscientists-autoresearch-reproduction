---
name: throughput-findings
description: Cycle-1 measured results — 3 KEEPs on step-increasing / per-step-cost levers
type: feedback
---

All runs: 300s training budget, RTX 4080S 32GB, seed 42, DEVICE_BATCH_SIZE=64.

| experiment | change | steps | tok/s | val_bpb | outcome |
|---|---|---|---|---|---|
| baseline_shared (gpu2) | upstream, device batch 64, total 2**19 | 196 | 322K | 1.192708 | baseline |
| baseline_shared_hw (gpu1) | identical code, GPU 0 | 193 | 317K | 1.195744 | noise pair |
| exp_tput_batch_2e18 | TOTAL_BATCH_SIZE 2**18 (grad_accum 2) | 374 | 316K | 1.169258 | KEEP |
| exp_tput_mlp_exp_3 | MLP_EXPANSION 4 -> 3 (-10.5% FLOPs) | 410 | 348K | 1.158107 | KEEP |
| exp_tput_compile_autotune | compile max-autotune-no-cudagraphs | 433 | 368K | 1.147892 | KEEP |

Key facts:
- Same-code noise between two identical GPUs = 0.003036 val_bpb. Do not promote |delta| < ~0.003 on one seed.
- Loss was still decreasing in the final 20% of every run (drop 0.13-0.15), i.e. every config is undertrained
  at 300s. Step-increasing levers keep paying off; this validates the throughput team hypothesis.
- `mfu_percent` is normalized to H100 peak (989.5 TFLOP/s) and is meaningless on a 4080S — ignore it.
- Cumulative champion improvement this cycle: 1.192708 -> 1.147892 (-0.044816).
