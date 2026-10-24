---
name: finding_muon_ramp_anchor
description: Upstream reference run for this exact config = 953 steps/300s, so the 300-step momentum ramp is ~31% of a reference run and may never complete on slower GPUs
type: finding
---

Upstream `repo/program.md` shows the example run for the SAME config as our
champion (50.3M params, 2**19 TOTAL_BATCH_SIZE, DEPTH=8): `num_steps: 953`,
`val_bpb: 0.997900`, `peak_vram_mb: 45060.2`, `mfu_percent: 39.80`.

Consequences (verified against champion/train.py):
- `get_muon_momentum(step)` ramps 0.85->0.95 over 300 steps = ~31% of the
  reference run. Intentional shape: terminal momentum after ~1/3 of training.
- On 2x RTX 4080S 32GB, DEVICE_BATCH_SIZE=128 OOMs (needs 64) and per-step
  wall time is several-fold higher, so 300s likely completes only ~100-200
  steps. Then frac = step/300 = 0.33-0.67, momentum = 0.883-0.917: terminal
  value never reached. Raising the target 0.95->0.98 changes actual momentum by
  only ~0.01 at 100 steps (inside the 0.003 bpb noise band).
- Fix filed as exp_gq_muon_ramp_progress: progress-based ramp `progress/0.3`
  (300/953 ~= 0.315), which reproduces the reference shape on any hardware and
  matches the code comment "Schedules (all based on progress = training_time /
  TIME_BUDGET)". The call site must change from `get_muon_momentum(step)` to
  `get_muon_momentum(progress)`.
