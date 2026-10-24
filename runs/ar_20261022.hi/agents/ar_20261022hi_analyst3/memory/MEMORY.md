# Memory Index

- [Task dynamics cycle 1](task_dynamics_cycle1.md) — depth=scale axis, ~50.3M params, step budget ~100-150, Muon-vs-AdamW LR scaling asymmetry.
- [Cycle 2 step dominance](cycle2_step_dominance.md) — more optimizer steps is the only KEEP mechanism so far; ~0.00014 val_bpb/step; determinism under seed 42.
- [Shared-file write race](feedback_shared_file_writes.md) — GET before initializing shared files; recover overwritten versions with ?version=N.
- [Step saturation](feedback_step_saturation.md) — 719->1396 steps is FLAT; only step-neutral per-step-quality probes can KEEP now.
- [Param accounting + activation decomposition](task_param_accounting.md) - vocab is 8192 (wte 4.19M, VE 16.8M=33%, MLP ~42% of FLOPs); ReLU^2 splits into rectifier vs squaring.
