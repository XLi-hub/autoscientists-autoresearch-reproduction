---
name: step-budget-calibration
description: Why schedule constants calibrated in optimizer steps are suspect in the 300s autoresearch budget
type: finding
---

# Step-budget calibration finding (cycle 1, 2026-10-22)

Champion geometry: DEPTH=8 -> model_dim=512, 4 heads x 128, ~50M params, seq 2048, TOTAL_BATCH_SIZE=2**19 tokens/step, TIME_BUDGET=300 s.

Derived: ~3.75e8 flops/token; at 25-40% MFU on an RTX 4080S (~195 TFLOP/s bf16 dense) this is ~2.5-5 s/step, i.e. roughly **60-120 optimizer steps per run**.

Consequences (all testable, zero compute cost):
- `get_muon_momentum`: `frac = min(step/300, 1)` => momentum ends at 0.85 + 0.1*(steps/300) ~ 0.87-0.89; the designed 0.95 is never reached. Ramp is calibrated for runs of thousands of steps.
- `WARMDOWN_RATIO = 0.5` therefore decays the LR over the last ~30-60 steps, i.e. it is a large fraction of total parameter movement, unlike in a long run.
- `gc` every 5000 steps never triggers.

Reporting bug: `H100_BF16_PEAK_FLOPS = 989.5e12` is hardcoded; on 4080S the printed mfu is ~5x understated (reporting only, not val_bpb).

Verification path: count `num_steps:` in the first baseline result file. If steps >> 300, discard this finding.
