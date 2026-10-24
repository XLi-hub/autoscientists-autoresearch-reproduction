---
name: ar-20261024-run-outcome
description: "How run ar_20261024 ended (stagnation stop), final champion, and the one untested lever"
metadata:
  node_type: memory
  type: project
  originSessionId: 82136335-4b1d-419b-ac36-d8c4dbd9b0be
  modified: 2026-10-24T08:57:19.258Z
---

Run `ar_20261024` (task-autoresearch, 2x RTX 4080S) stopped on 2026-10-24 by the task profile's
stagnation rule: 0 KEEPs in the last 10 completed experiments.

- Final champion `exp_tput_batch_2e17`, val_bpb **1.088286** (seed baseline 1.192708, −8.8%),
  `champion/train.py` sha1 `e102f683…`. Path: MLP_EXPANSION 2, TOTAL_BATCH_SIZE 2**17, DEVICE_BATCH_SIZE 64,
  compile `max-autotune-no-cudagraphs`, ASPECT_RATIO 64, HEAD_DIM 128.
- 24 experiments + 1 calibration, 6 KEEPs. Calibrated same-code sigma ≈ 0.0023–0.0025, so the 2σ gate is ≈0.005.
- Every remaining fine-grain channel measured flat *inside that gate*: optimizer/EMA horizons, MATRIX_LR
  bracket, WEIGHT_DECAY bracket, value-embedding density, width/AR bracket, head_dim, window pattern.
  WEIGHT_DECAY is flat for a schedule reason worth remembering: `wd(p)=WD*(1-p)` with WARMDOWN_RATIO=0.5
  zeroes the shrink before the run's midpoint while the metric is read on end-of-run weights.
- Never tested (queued when the loop stopped): `exp_tput_loss_head_precision` (chunked fp32 CE, the only
  >3% tok/s lever at bit-identical function), `exp_cap_head_dim_256`, `exp_gq_wd_schedule_const`.
- Full write-up: `<run>/logs/FINAL_REPORT.md`; per-agent notes live in each `agents/*/memory/`.

**Why:** a future session resuming this run should not re-derive why the obvious HP knobs are flat, and
should know which single lever was parked rather than falsified. See [[autoresearch-run-env-facts]].
**How to apply:** to resume, dispatch one GPU agent per device on the three queued items; expect ~0.005
resolution only.
