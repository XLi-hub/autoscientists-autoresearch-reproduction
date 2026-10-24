---
name: finding_step_coupled_constants
description: The three throughput KEEPs changed the optimizer step count 193->433, which re-scales every optimizer constant defined in STEPS (Adam betas, muon ramp); wall-clock schedules are unaffected
type: finding
---

Champion history on 2026-10-24 (val_bpb 1.192708 -> 1.169258 -> 1.158107 -> 1.147892):
- TOTAL_BATCH 2**19 -> 2**18: 193 -> 374 steps, -0.023450
- MLP 4x -> 3x: 374 -> 410 steps, -0.011151
- compile max-autotune: 410 -> 433 steps, -0.010215

All three won the same way: more optimizer steps in the fixed 300 s budget. The 2**18
KEEP won while processing FEWER tokens (98.0M vs 101.2M), so val_bpb responds to update
count, not token count. The run is still undertrained (final-20% loss drop 2.3-2.6% of
range, no plateau).

Consequence, reusable: constants whose meaning is measured in STEPS silently change
effective scale when the step count changes. Here:
- Adam betas (0.8, 0.95) have memory 1/(1-beta) = 5 / 20 steps; the 2.24x step increase
  means they now cover 2.24x less of training. Filed as exp_gq_adam_betas_bracket.
- get_muon_momentum uses step/300; at 433 steps terminal momentum is reached at 69% of
  the run (upstream intent ~31%). exp_gq_muon_ramp_progress is now a larger perturbation.
- get_lr_multiplier and get_weight_decay use wall-clock progress (training_time/TIME_BUDGET)
  and are NOT rescaled by the step-count change — do not "fix" them as if they were.
