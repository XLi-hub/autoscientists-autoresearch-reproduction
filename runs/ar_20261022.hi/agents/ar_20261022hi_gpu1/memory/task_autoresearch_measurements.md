---
name: task-autoresearch-measurements
description: Measured val_bpb/throughput facts for the autoresearch loop on this hardware
type: finding
---

# Measured facts (updated 2026-10-22 cycle 3, GPU 0, RTX 4080S)

## Runs completed by this agent
| exp | change | val_bpb | num_steps | tokens(M) | outcome |
|---|---|---|---|---|---|
| baseline_shared | upstream + DEVICE_BATCH_SIZE 64 | 1.195701 | 193 | 101 | baseline |
| exp_batch_2e18 | TOTAL_BATCH_SIZE 2**19 -> 2**18 | **1.170054** | 373 | 97.8 | KEEP |
| exp_warmdown_025 | WARMDOWN_RATIO 0.5 -> 0.25 | 1.176817 | ~373 | ~98 | DISCARD |
| exp_gqa_kv1 | n_kv_head 4 -> 1 (GQA 4:1) | 1.102620 | 784 | 102.8 | DISCARD (+0.0086) |
| exp_wd_0p0 | WEIGHT_DECAY 0.2 -> 0.0 (Muon) | 1.094875 | 729 | 95.6 | DISCARD in-band |

Champion at end of cycle 3: **exp_batch_2e17, val_bpb=1.094037, 719 steps, 94.2M tokens,
TOTAL_BATCH_SIZE=2**17, DEVICE_BATCH_SIZE=64, DEPTH 8, width 512, 50.3M params.**

## Hardware throughput
- At TOTAL_BATCH_SIZE=2**17 (grad_accum=1, 64x2048 tokens/step): ~313-337k tok/s,
  ~419 ms/step (batch 2**17) — 719 steps / 94.2M tokens in 300 s.
- Real MFU ~73% of the card's dense-bf16 peak; `mfu_percent` in the log uses the H100
  constant (989.5e12) and prints ~7.5%, multiply by ~9.5 for the true value.
- `peak_vram_mb` 22653 MB at width 512 / batch 64 (unchanged by wd); GQA-1 dropped it to
  19847 MB. DEVICE_BATCH_SIZE=128 OOMs.
- Full run wall ~355-390 s (300 s training + ~55-90 s startup/eval).

## The step lever saturates at ~719 steps
- 2**19 -> 2**18: 193 -> 373 steps, -0.0256 (8.5x band) KEEP.
- 2**18 -> 2**17: 373 -> 719 steps, -0.0760 KEEP.
- 2**17 -> 2**16: 719 -> 1396 steps at identical tokens, +0.0003 FLAT (inside band).
- GQA-1: 719 -> 784 steps via -7.9% FLOPs/token, **+0.0086 WORSE**. The step arithmetic
  arrived but a per-token K/V capacity cost (~+0.011 bpb) dominated: the block-mean loss
  was worse than champion from 20% of the run onward. Step gains bought by cutting
  attention capacity do NOT pay.
- Conclusion: the run is no longer step-starved past ~719 updates. Further wins must come
  from per-token quality at fixed steps (optimizer/regularization/schedule), not more updates.

## Noise floor (empirical, first measurement)
gpu2's same-code two-seed pair for exp_warmdown_070: 1.093748 (seed 42) vs 1.097886 (seed 43),
|spread| = 0.004138. The old 0.003 conservative band is too tight; treat single-run deltas
below ~0.008 as unconfirmed. `torch.manual_seed(42)` is hardcoded, so multi-seed runs need an
explicit one-line seed edit.

## Axes with known outcomes
- warmdown: 0.25 DISCARD (-0.0068), 0.5 champion, 0.7 flat/worse (2 seeds) -> optimum ~0.5.
- warmup 0.1: DISCARD +0.0278 (warmup wastes budget).
- aspect ratio: 32 DISCARD (+0.0088, width 256 capacity-limited), 80 predicted DISCARD.
- depth 10: DISCARD (+0.0975, -41% steps). value embeddings all layers: DISCARD (+0.0060).
- weight decay 0.2 -> 0.0: flat (+0.0008), axis OPEN (wd=0.4 is the only untested arm).
- n_kv_head: 4 -> 1 DISCARD (+0.0086). Ratio 2 (2:1) is the suggested bracket partner.
