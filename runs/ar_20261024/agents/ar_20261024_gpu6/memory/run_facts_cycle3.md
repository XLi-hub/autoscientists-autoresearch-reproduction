---
name: run-facts-cycle3
description: exp_cap_head_dim_64 result, champion schema quirk, and training wall-clock for gpu6
type: project
---

- `exp_cap_head_dim_64` (HEAD_DIM 128->64, n_head 4->8, width 512 held): val_bpb **1.096009** vs
  champion 1.088286 -> **DISCARD**, delta +0.007723 (2.70 sigma). Steps 948 vs 956 (step-neutral,
  as predicted), tok/s 408.5K vs 411.3K, params 41.9M (+512 ve_gate). Keep HEAD_DIM=128.
- `exp_cap_ar48_b2e17` (gpu3, same cycle) landed DISCARD 1.088598 (+0.0003, inside noise):
  ASPECT_RATIO 48 does NOT stack onto TOTAL_BATCH_SIZE 2**17. Combined with exp_tput_batch_2e16
  (1.085575, inside noise), the step-count channel is saturated at 2**17.
- **champion.md schema quirk:** the metric lives under `metric_value:`, not under a `<metric_name>:`
  key. `champ.get(metric_name, inf)` from the HEARTBEAT template returns inf here and would mark any
  run as KEEP. Use `float(champ["metric_value"])`.
- Training wall-clock at this config: **~484s** total = 300.1s training + ~164s compile/startup +
  ~20s eval. max-autotune re-benchmarks new attention shapes (~100s extra after a head_dim change).
  Launch as a background Bash task and block on `kill -0 <pid>` in a foreground loop.
- Noise floor: sigma 0.002865, 2-sigma 0.00573 (still measured on the 1.19-era base).
