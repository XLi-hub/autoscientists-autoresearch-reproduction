---
name: step-count-dominates-attention-is-free
description: On this 300s nanoGPT task val_bpb tracks optimizer steps; attention-layout changes are throughput-free
type: finding
---

# val_bpb is step-count dominated; attention FLOPs are nearly free on a 4080S

Measured on 2026-10-24 (champion lineage, single seed each):

| change | val_bpb | steps |
|---|---|---|
| baseline (batch 2**19, MLP 4) | 1.192708 | ~410 |
| TOTAL_BATCH_SIZE 2**19 -> 2**18 | 1.169258 | ~410 |
| MLP_EXPANSION 4 -> 3 | 1.158107 | 410 |
| torch.compile max-autotune-no-cudagraphs | 1.147892 | 433 |
| MLP_EXPANSION 3 -> 2 (gpu4) | 1.132007 | ~486 |
| **ASPECT_RATIO 64 -> 48 (width 512 -> 384)** | **1.094760** | **632** |
| WINDOW_PATTERN SSSL -> SSLL | 1.152771 | 429 (vs 433) |
| WARMDOWN_RATIO 0.5 -> 0.25 | 1.16297 | same |

Two robust facts:

1. **Every step-cheapening change KEEPs, roughly proportional to the step gain.** The
   model is heavily undertrained (113-166M tokens for a 31-46M-param model; final-20%
   loss still dropping ~0.15). Cut per-token cost and you win.
2. **`estimate_flops()` is not a step predictor for attention axes.** Window SSSL->SSLL
   is +5.88% estimated FLOPs/token but measured only -0.9% steps and -1.0% tok/s:
   attention at seq 2048 / width 512 is memory/kernel-bound on the 4080S, not
   compute-bound. It *is* roughly right for width/MLP changes (matrix dominated), which
   is why AR48 gave +46% steps for a -36% FLOP estimate (less than proportional: 677
   predicted vs 632 measured).

Practical guidance for the next data point on the width axis: the win came from making
the model *smaller/faster*, not from representational structure (zero-cost head_dim/window
probes gave nothing). Expect the optimum to be somewhere below width 384; test AR32
(width 256) rather than re-testing structure.
