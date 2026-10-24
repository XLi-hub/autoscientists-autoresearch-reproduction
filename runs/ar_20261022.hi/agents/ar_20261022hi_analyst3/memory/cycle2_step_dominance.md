> **SUPERSEDED 2026-10-22 by feedback_step_saturation.md.** The claim below (more steps is the
> only KEEP mechanism, ~0.00014 val_bpb/step) held only up to ~719 steps. exp_batch_2e16 showed 719 -> 1396
> steps is FLAT (+0.00032), so the slope is not global. Keep for the 373->719 calibration only.

---
name: cycle2-step-dominance
description: Cycle-1 evidence that optimizer-step count, not per-step quality, dominates val_bpb at the 300 s budget
type: finding
---

# Step count dominates at this token budget (cycle-1 evidence)

- batch 2**19 -> 2**18 (193 -> 373 steps, identical tok/s, tokens, VRAM): val_bpb 1.195701 ->
  1.170054, delta +0.025647. The only KEEP of the run.
- warmdown 0.5 -> 0.25 (same steps, more full-LR steps, shorter decay): 1.176817, **worse** by
  0.006763. So "more full-LR steps" is not the mechanism; more *total* optimizer steps under an
  intact decay schedule is.
- warmup 0.1 (costs ~10% of the 300 s budget): 1.223462, worse by 0.027761.
- Muon momentum ramp 300 -> 60: 1.174107, worse by 0.004053 (1.35x the canonical 2-sigma 0.003).

Implied exchange rate: ~0.00014 val_bpb per optimizer step near 373 steps. Any change that costs
>10-15% of steps must buy >0.015-0.02 val_bpb to KEEP — a very high bar. Capacities that are
step-neutral (extra value-embedding layers, HEAD_DIM shape) face no such headwind and are the
cheapest structural probes.

Reproducibility: same code path + torch.manual_seed(42) makes the loss trajectory bit-identical
(verified by exp_warmdown_025 vs exp_batch_2e18 up to schedule divergence). Run-to-run variation
comes from step-count jitter (+/-1.5% at fixed 300 s), not weight init.
