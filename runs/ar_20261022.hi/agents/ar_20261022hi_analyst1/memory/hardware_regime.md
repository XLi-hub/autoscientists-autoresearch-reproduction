---
name: hardware-regime
description: 4080S 5-min budget yields ~90 optimizer steps, ~45M tokens, and the pristine config exceeds 32.7 GB VRAM
type: finding
---

# Compute regime on 2x RTX 4080S (32.7 GB each), TIME_BUDGET=300 s

FACTUAL FINDINGS (verified from champion code + upstream docs, not yet measured on this box):

1. **VRAM**: upstream `repo/program.md` baseline summary for the pristine config (DEPTH 8,
   DEVICE_BATCH_SIZE 128) reports `peak_vram_mb: 45060.2`. These cards have 32760 MB. Peak activation
   memory is linear in DEVICE_BATCH_SIZE, so the pristine config should OOM; batch 64 -> ~22 GB,
   depth 6 (dim 384) at batch 128 -> ~25 GB. Unverified empirically as of cycle 1.
2. **Step count**: 237M flops/token x 2**19 tokens = 1.24e14 flops/optimizer step. At ~36-40 TFLOPS
   effective (RTX 4080S ~104 TFLOPS dense bf16) that is ~3.1-3.4 s/step -> **~88-95 steps, ~45-50M
   tokens in 300 s**, vs the H100 baseline's 953 steps / 499.6M tokens.
3. **Parameter budget**: 50.3M params against ~45M tokens is ~1 token/param (H100: 10; Chinchilla-
   optimal: ~20) => the model is heavily over-parameterized for the token budget.
4. **Mis-scaled constants**: `get_muon_momentum` ramps `min(step/300,1)` (never passes ~0.88 in ~90
   steps); WARMDOWN_RATIO=0.5 is wall-clock based, so ~44 of ~88 steps are spent decaying.
5. **Instrumentation trap**: `mfu_percent` is computed against H100_BF16_PEAK_FLOPS=989.5e12, so it
   reads ~9.5x low on this hardware. `peak_vram_mb` is the binding resource, not MFU.
6. Eval cost is outside TIME_BUDGET: EVAL_TOKENS=21M at batch 128 = 80 forward batches.

CORRECTION (cycle 4, measured): point 2's "~90 steps" holds only at TOTAL_BATCH_SIZE=2**19. At the
champion 2**17 the run does **719 steps / 94.2M tokens** in 300 s. Measured throughput is ~314k
tok/s = ~72% of the ~104 TFLOPS bf16 peak (the logged `mfu_percent` reads ~9-10 because it divides by
the H100 constant - ignore it). Peak VRAM at DEPTH 8 / DEVICE_BATCH_SIZE 64 is ~22.7 GB = 69% of
32.7 GB; DEVICE_BATCH_SIZE 128 OOMs. Throughput is compute-bound, so the remaining lever is faster
kernels/compile, not memory.
