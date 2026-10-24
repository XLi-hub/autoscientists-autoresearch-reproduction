---
name: ar_20261022hi_gpu3
role: gpu
team: gradient-quality
gpu: 1
server: server2
last_seen: "2026-10-22T16:35:56.409582+00:00"
session_count: 2
last_branch: "normal"
last_experiment: "exp_adam_eps_hi"
last_outcome: "DISCARD"
last_val_bpb: 1.098069
---

# ar_20261022hi_gpu3

GPU agent (CUDA_VISIBLE_DEVICES=1). Team: gradient-quality (H-gradient-quality).

## Current Focus
Ran three single-seed arms on GPU 1 this cycle, all DISCARDs, champion unchanged at exp_batch_2e17 = 1.094037:
- exp_matrix_lr_lo (0.04->0.02): 1.097159, +1.03 sigma -> tie.
- exp_matrix_lr_hi (0.04->0.08): 1.102942, +2.95 sigma -> real negative. **matrix_lr bracket CLOSED at 0.04.**
- exp_adam_eps_hi (1e-10->1e-6): 1.098069, +1.34 sigma -> tie, but with a real EARLY transient (step-142 loss
  4.127 vs 3.827 reference) that fully recovers by step ~360.

## Notes for Next Session
- Matrix LR is exhausted: both arms worse, curve asymmetric (steeper high). Do not re-probe 0.02/0.08.
- AdamW eps is a transient, not a no-op: judge any future eps probe on the EARLY loss curve, not final val_bpb.
  The queued 1e-8 control arm is 100x from 1e-10 and predicted sub-band - deprioritize.
- Still-open high-priority arms, in my recommended order: exp_adam_beta1_hi (0.8->0.9; last untested moment on
  50% of params), then exp_muon_ramp_900. Both were left for gpu4/other rotations; I reviewed their proposals.
- Practical: runner is agents/ar_20261022hi_gpu3/workspace/run_exp.py (writes the sentinel, blocks on subprocess.run,
  parses nothing). Invoke with /root/autodl-tmp/envs/ar/bin/python3, CUDA_VISIBLE_DEVICES=1,
  HF_HOME=/root/autodl-tmp/ar_20261022.hi/.cache/huggingface, HF_HUB_OFFLINE=1. One run = ~362 s wall (300 s train).
- The 2-sigma band is 0.00604; nothing from these three arms is promotable individually.
