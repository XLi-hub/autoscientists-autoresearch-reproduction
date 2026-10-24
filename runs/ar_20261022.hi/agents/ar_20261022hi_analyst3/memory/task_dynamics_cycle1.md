---
name: task-dynamics-cycle1
description: Load-bearing structural facts about the autoresearch champion (depth/width coupling, param counts, LR scaling asymmetry, step economics)
type: finding
---

# Autoresearch nanogpt — structural facts (verified by reading champion/train.py, cycle 1)

**Depth is a scale axis, not a layer count.** `build_model_config` computes
`model_dim = ceil(depth*ASPECT_RATIO / HEAD_DIM)*HEAD_DIM`, so with ASPECT_RATIO=64,
HEAD_DIM=128: DEPTH 6/8/10 -> n_embd 384/512/640 and n_head 3/4/5. Never describe a
depth experiment as "one more layer" — it moves width and total params too.

**Parameter budget at DEPTH=8 (n_embd 512, vocab 8192):** ~50.3M total.
- transformer blocks 25.2M (attn 8.4M, MLP 16.8M)
- wte 4.19M, lm_head 4.19M
- value embeddings 16.8M (**33% of the model**, 4 layers x 8192x512)
DEPTH=10 -> ~85.9M (+70%); DEPTH=6 -> ~26.3M (-48%).

**Step economics:** TOTAL_BATCH_SIZE=2**19, DEVICE_BATCH_SIZE=128, MAX_SEQ_LEN=2048 ->
grad_accum=2. At 300s and ~50M params, expect on the order of 100-150 optimizer steps
(order-of-magnitude estimate, not measured). `step > 10` is excluded from TIME_BUDGET
accounting => ~10 steps of free compute. WARMDOWN_RATIO=0.5 means the last ~50% of steps
run at linearly decaying LR.

**LR scaling asymmetry (important confounder):** `dmodel_lr_scale=(n_embd/768)**-0.5` is
applied to the AdamW groups only (lm_head, wte, value_embeds). Muon matrix_lr=0.04 is NOT
scaled. At n_embd=512 AdamW LRs are effectively 1.2247x their 768 reference; at 640, 1.0954x;
at 384, 1.4142x. So depth/width experiments confound capacity with AdamW-vs-Muon LR ratio.

**Other inline (Layer-3) literals nobody sweeps:** MLP hidden multiplier `4 * config.n_embd`,
ve_gate_channels=32, rotary base=10000, rotary_seq_len=seq*10, logit softcap=15,
Muon momentum ramp `min(step/300,1)` (never completes in ~120 steps), gc.collect every 5000
steps (never reached), H100_BF16_PEAK_FLOPS=989.5e12 (MFU reporting only — meaningless on
4080S, do not treat low reported MFU as a real utilization signal).

**Has_ve:** returns `layer_idx % 2 == (n_layer-1) % 2`, i.e. 4 of 8 layers at DEPTH=8
(layers 1,3,5,7), 5 of 10 at DEPTH=10, 3 of 6 at DEPTH=6.
