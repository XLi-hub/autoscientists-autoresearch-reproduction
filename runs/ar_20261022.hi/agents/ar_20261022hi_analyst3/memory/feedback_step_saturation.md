---
name: step-saturation-regime
description: The optimizer-step lever saturates at ~719 steps (719->1396 is flat); rank probes by per-step quality now.
type: feedback
---

# Step saturation (confirmed 2026-10-22, cycle 3)

Evidence:
- exp_batch_2e18: 2**19->2**18, 193->373 steps, val_bpb 1.195701 -> 1.170054 (KEEP +0.0256)
- exp_batch_2e17: 2**18->2**17, 373->719 steps, 1.170054 -> 1.094037 (KEEP +0.0760)
- exp_batch_2e16: 2**17->2**16, 719->1396 steps, 1.094037 -> 1.094356 (**FLAT +0.00032**)

Fitted slope only holds below the knee: 0.1159 val_bpb per ln(step) over 373->719, ~0.000 over 719->1396.

Consequences that burned three proposals this run:
- A proposal justified by "+X% steps" is worth ~0 unless its step target lands below ~700.
- Trading capacity for steps is pre-falsified: aspect_ratio_32 (-0.0088 at +142% steps), depth_10 (-0.0215 at -41% steps).
- Spend slots on step-neutral per-step-quality probes: activation, HEAD_DIM, value-embedding count.

Process lesson: a proposal can be invalidated by a result that lands *after* it is written. Re-check the
newest RESULTs immediately before queueing, and publicly withdraw rather than queue a dead premise.
