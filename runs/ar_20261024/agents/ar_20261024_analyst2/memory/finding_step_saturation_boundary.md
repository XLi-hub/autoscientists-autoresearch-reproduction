---
name: finding_step_saturation_boundary
description: Return per optimizer update collapses ~16x between a 487-step base and a 956-step base; proven unconfounded by two pure batch-size doublings, so "cheaper step" is a dead lever at the current champion
type: finding
---

Measured 2026-10-24 at champion `exp_tput_batch_2e17` (val_bpb 1.088286, 41.94M
params, 956 updates, 125.3M tokens, 2**17 batch).

Two comparisons change ONLY TOTAL_BATCH_SIZE, so the model is bit-identical and
there is NO capacity confound:

| lever | base -> new steps | Δbpb | per +10% steps |
|---|---|---|---|
| 2**18 -> 2**17 | 487 -> 956 | -0.043721 | -0.00454 |
| 2**17 -> 2**16 | 956 -> 1854 | -0.002711 | -0.00029 |

Same lever, same ~+95% step gain, 16x less return. Across seven paired arms the
boundary is sharp: base <= 487 returns -0.0045 to -0.0116 bpb per +10% steps;
base >= 632 returns +0.0028, +0.00008, or -0.00029. The saturation belongs to the
BASE's step count, not to the lever.

Corroborated on a second (width) axis: AR 64->48 gave -0.053132 at a 433-step
base and +0.000312 at a 956-step base. Same relative lever, opposite sign, base
step count the only changed variable. 28.31M params matched 41.94M to 0.0003.

Consequences, reusable:
- Do not queue step-gain levers (batch reductions, width reductions, window
  changes, FLOPs/token cuts) at a base above ~600 steps. Price their step gain at
  the dead-zone slope (~+0.00008 bpb per +10% steps, i.e. ~0).
- Conversely, capacity-UP arms that "lose steps" (AR80, MLP5) are no longer
  penalised: their step penalty is ~0.0003. They are the clean capacity-UP
  instruments.
- A null from a cheap-step experiment at a high base is NOT evidence of a
  capacity floor — the step channel explains it without invoking capacity.
- Remaining live dimension is per-step quality (optimizer/LR/schedule shape).
  Largest untouched knob here: MATRIX_LR = 0.04 (Muon group = 16.78M of 20.97M
  FLOP-relevant params = 80%). Never varied on any base.

Calibration aid: the analytic predictor (6*(params - wte - VE - scalars) +
attention) reproduces published anchors exactly and predicts step counts to
mean |error| 4.9%, max 8.3%. Use +-10% when sizing far probes. Do NOT infer
attention-layout effects from a 6N-only model: SSLL missed +4.9% and AR48 -6.7%,
opposite signs — a +-8% predictor, not a directional rule.
