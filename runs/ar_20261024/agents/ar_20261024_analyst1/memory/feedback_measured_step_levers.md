---
name: measured_step_levers
description: Measured per-axis val_bpb deltas, the 2-sigma noise gate, and the step-count mechanism of the throughput team
type: feedback
---

# Measured throughput levers (ar_20261024, cycle 2)

Champion after cycle 2: exp_tput_compile_autotune = 1.147892 (baseline 1.192708). Counted steps
193 -> 374 -> 410 -> 433 across the three KEEPs, each delta far larger than noise.

| axis | value | exp_id | val_bpb | paired delta | verdict |
|---|---|---|---|---|---|
| total_batch_size | 2**18 | exp_tput_batch_2e18 | 1.169258 | -0.023450 | KEEP |
| mlp_expansion | 3 | exp_tput_mlp_exp_3 | 1.158107 | -0.011151 | KEEP |
| compile_mode | max-autotune-no-cudagraphs | exp_tput_compile_autotune | 1.147892 | -0.010215 | KEEP |
| warmdown_ratio | 0.25 | exp_gq_warmdown_025 | 1.162970 | +0.004863 (vs 1.158107 base) | DISCARD but inside 2-sigma |
| muon_momentum | 0.98 | exp_gq_muon_mom_098 | 1.192527 | +0.000181 | flat |

Noise floor: 3 same-code pairs (0.003036, 0.004219, 0.004716) -> pooled sigma 0.002865, 2-sigma
0.00573. NOT locked until n>=5. Any delta below ~0.006 is unconfirmed and needs a second seed before
promotion or refutation.

Mechanism: the model is compute-bound at the fixed 300 s budget, so lowering per-step cost or the
update interval buys more optimizer steps, and steps dominate. The batch 2**18 KEEP is the decisive
evidence: it cut tokens per step yet improved, so what matters is update count, not tokens seen.

Live proposals: exp_tput_batch_2e17 (2**17, grad_accum 1, ~830-860 steps) and exp_tput_win_short_4
(short window //4, -8.8% FLOPs/token). Both are parameter-free so they isolate step count from
capacity; any MLP/depth change is capacity-confounded.
