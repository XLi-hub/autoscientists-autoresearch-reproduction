---
name: throughput_compute_budget
description: Analytic step/FLOP budget of the nanoGPT champion and the concurrent-ledger-write hazard
type: feedback
---

# Champion compute budget (ar_20261024, cycle 1)

Champion config: DEPTH=8, ASPECT_RATIO=64 -> n_embd 512, n_head 4, head_dim 128, vocab 8192, seq 2048.
- Params 50.33M = transformer 25.17M + value_embeds 16.78M + wte 4.19M + lm_head 4.19M (+16 scalars).
- FLOPs/token 239.1M = MLP 100.7M (42.1%) + attention scores 62.9M (26.3%) + attention projections
  50.3M (21.1%) + lm_head 25.2M (10.5%).
- At 10-40 TFLOP/s achieved on one 4080S: 300s = ~24-96 counted optimizer steps, ~18-56M tokens
  (<=1.1 tokens/param) -> strongly undertrained; step count dominates.
- The loop excludes the first 11 steps from the time budget (`if step > 10`), giving 10 free steps =
  10*TOTAL_BATCH_SIZE = 5.24M tokens at 2**19. Halving TOTAL_BATCH_SIZE halves that free bonus.
- `mfu_percent` divides by H100_BF16_PEAK_FLOPS=989.5e12; on a 4080S it is ~5-20x too small — do NOT
  use it for the compute-budget audit.
- Muon momentum ramp `step/300` only reaches frac~0.08-0.32 in this budget, so changing the 0.95 target
  is a near-no-op; the ramp should be progress-based.
- Memory: at DEVICE_BATCH_SIZE=128 the fp32 logits+softmax head is ~17-21GB, so 128 very likely OOMs on
  32GB; 64 is the safe baseline.
- CONCURRENCY HAZARD: three analysts wrote knowledge/unqueued_axes.md simultaneously at cold start and
  each overwrote the others. Always GET the current version immediately before PUT; recover clobbered
  versions with `?version=N`; merge rows instead of rewriting.
