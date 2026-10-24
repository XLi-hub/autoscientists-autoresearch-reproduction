---
name: ar_20261022hi_gpu5
role: gpu
team: capacity
last_seen: "2026-10-22T16:36:21.855224+00:00"
session_count: 2
last_branch: "normal"
last_experiment: "exp_activation_silu"
last_outcome: "DISCARD"
gpu: 0
---

# ar_20261022hi_gpu5

GPU agent on GPU 0. Team: capacity (H-capacity).

## Current Focus
Cycle 5 ran two step-neutral structural/representational probes on champion exp_batch_2e17 (val_bpb 1.094037):
1. **exp_head_dim_64** (HEAD_DIM 128->64, n_head 4->8): val_bpb 1.100821, delta +0.006784 (2.25 sigma) -> DISCARD.
   Identical params/FLOPs/steps, so it is a real per-step-quality loss. The gap is an early-training
   transient: +0.3225 nats at step 100 decaying monotonically to +0.0062 at step 700.
2. **exp_activation_silu** (ReLU^2 -> SiLU^2, square preserved): seed42 1.092775 (would have been a KEEP),
   seed43 1.095855 (worse). Multi-seed gate fired -> DISCARD in-band tie, champion NOT promoted.
   Appended the 3rd seed pair; pooled sigma 0.003019 -> 0.002767 (2-sigma 0.00553).

Champion is UNCHANGED at 1.094037 (exp_batch_2e17) after this cycle.

## Notes for Next Session
- ALWAYS run train.py with HF_HOME=/root/autodl-tmp/ar_20261022.hi/.cache/huggingface and HF_HUB_OFFLINE=1,
  and use /root/autodl-tmp/envs/ar/bin/python3 directly (do NOT use `uv run`: the shared uv cache deadlocks).
- Re-copy champion/train.py from /root/autodl-tmp/ar_20261022.hi/champion at the start of every cycle.
- Write the compute-mode claim (logs/ar_20261022hi_gpu5.gpu_claim) before claiming from the queue.
- Remaining capacity queue: exp_ve_none (high), exp_head_dim_256 (high, discussion-gated for 15 min after posting),
  exp_mlp_expansion_6 (low). exp_head_dim_256 is the informative opposite arm of this cycle's head_dim result.
- Any result with |delta| < 0.00553 MUST be confirmed on a second seed (torch.manual_seed 43) before promotion.
