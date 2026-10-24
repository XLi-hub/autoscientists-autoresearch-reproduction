---
name: ar_20261024_gpu11
role: gpu
team: gradient-quality
gpu: 1
last_seen: "2026-10-24T08:56:48.625941+00:00"
session_count: 1
last_branch: "normal"
last_experiment: "exp_gq_weight_decay_hi"
last_outcome: "DISCARD"
last_val_bpb: 1.088286
---

# ar_20261024_gpu11

GPU agent on GPU 1 (CUDA_VISIBLE_DEVICES=1). Team: gradient-quality.

## Current Focus
Ran the full WEIGHT_DECAY bracket (0.1, 0.2, 0.4), two seeds per arm, and **closed the axis FLAT**:

- `exp_gq_weight_decay_lo` (0.1): seed 42 = 1.085846 (looked like a KEEP at -0.00244), seed 43 = 1.090242.
  2-seed mean 1.088044, delta -0.000242 (0.09 sigma). DISCARD.
- `exp_gq_weight_decay_hi` (0.4): seed 42 = 1.089911, seed 43 = 1.090324. 2-seed mean 1.090118,
  delta +0.001832 (0.76 sigma), both seeds same sign, seed spread only 0.000413. DISCARD.

Both arms inside 0.0050 -> the pre-registered falsification clause of TEAM-REFORMED (`5e7449da`) fires.
Posted `[HYPOTHESIS-FALSIFIED]` (baaba34a). The whole optimizer channel (betas EMA horizons + first-order
decay) is closed on this codebase. Champion unchanged at 1.088286 throughout.

## Notes for Next Session
- **No new experiments on this team until the hypothesis is re-derived.** The 3 remaining pending items
  are stale (`exp_gq_adam_beta1_lo/hi` are the explicitly retired EMA family; `exp_gq_warmdown_075` is
  out-of-hypothesis). Do not claim them.
- Highest-value untested knob, if a new gq hypothesis is written: **the decay SCHEDULE**, not the
  coefficient — `exp_gq_wd_schedule_const` (constant `WEIGHT_DECAY` instead of `WD*(1-progress)`).
  Rationale in `results/exp_gq_weight_decay_hi.md`: the applied shrink is zero before progress 0.5, so
  the coefficient arms could never have moved a final-state metric.
- Measurement caveat recorded in the noise ledger: same-code seed spread is **code-dependent**, not a host
  constant — lo arm 0.004396 vs hi arm 0.000413 on the same GPU. Do not tighten the gate off one tight pair.
- Runtime facts unchanged: plain `/root/autodl-tmp/envs/ar/bin/python train.py` (NOT `uv run`), with
  HF_HOME=/root/autodl-tmp/cache/huggingface and HF_HUB_OFFLINE=1. ~375-380 s wall per run.
