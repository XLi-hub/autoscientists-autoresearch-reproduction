---
name: ar_20261024_gpu6
role: gpu
team: capacity
gpu: 1
server: server3
last_seen: "2026-10-24T08:00:47.175653+00:00"
session_count: 1
last_branch: "normal"
last_experiment: "exp_cap_head_dim_64"
last_outcome: "DISCARD"
last_val_bpb: 1.096009
---

# ar_20261024_gpu6

GPU agent on GPU 1. Team: capacity.

## Current Focus
Capacity-hypothesis probes on champion exp_tput_batch_2e17 (val_bpb 1.088286, MLP_EXPANSION=2,
TOTAL_BATCH_SIZE 2**17, ASPECT_RATIO 64, compile max-autotune-no-cudagraphs).

## Notes for Next Session
- `exp_cap_head_dim_64` (HEAD_DIM 128->64, n_head 4->8) = DISCARD, val_bpb 1.096009, delta +0.0077
  (2.70 sigma). Step-neutral as designed (948 vs 956 steps). Keep HEAD_DIM=128.
- gpu3's `exp_cap_ar48_b2e17` also DISCARDED (1.088598, +0.0003 inside noise) — AR48 does NOT stack
  onto batch 2**17. Champion unchanged. AR=48 gain was step-driven, and the step channel is saturated.
- Next unclaimed capacity items: `exp_cap_ve_density_2` (step-neutral capacity isolation, THE clean
  control), `exp_cap_depth6_w512`, `exp_cap_ar80_w640`, `exp_cap_depth12_w512`.
- Highest-value remaining region per analysts: per-step quality (gq re-tests) and zero-FLOP controls.
- Practical: training wall is ~484s (300s budget + ~165s compile/startup + ~20s eval). Run it as a
  background Bash task then block on a wait loop; a 600s foreground call is too tight.
- champion.md stores the metric under `metric_value` (NOT a `val_bpb:` key). The HEARTBEAT
  `champ.get(metric_name)` recipe returns None here — read `metric_value` instead.
