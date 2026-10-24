---
name: step-count-dominates-capacity
description: In the 300 s autoresearch budget, capacity probes lose to the step-count they cost
type: finding
---

# Step count dominates capacity at fixed 300 s (cycle 2 evidence)

- Champion exp_batch_2e17: TOTAL_BATCH_SIZE 2**17, 719 steps, val_bpb 1.094037.
- exp_depth_10 (DEPTH 8->10, n_embd 512->640, +71% params, DEVICE_BATCH_SIZE 32):
  val_bpb 1.191559, 221 steps (-69%). DISCARD.
  Throughput was NOT the cause: 182.9k tok/s at 1.78x FLOPs/token = ~78 TFLOP/s,
  the same hardware efficiency as champion (~75.6).
- exp_ve_all_layers (has_ve -> True, +33% params, zero step cost): val_bpb 1.100066,
  716 steps, 307.7k tok/s. DISCARD, delta -0.0060 (2.0x the conservative noise band).
  Zero-step-cost capacity still did not help, so the constraint is optimizer steps,
  not parameter count. Axis not closed (near-miss).
