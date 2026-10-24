# Memory Index

- [GPU env: HF cache/offline](feedback_gpu_env.md) - train.py needs HF_HOME + HF_HUB_OFFLINE; run python3 directly, not uv
- [Step count dominates capacity](finding_step_count.md) - cycle-2 depth-10 and VE-all-layers evidence
- [Seed choice dominates residual](finding_seed_dominates.md) - n=3 seed pairs, sigma 0.00277, 2-sigma 0.00553; false-KEEP observed
- [Head-dim granularity](finding_head_dim.md) - 8x64 < 4x128 at identical params/FLOPs/steps; early-transient mechanism
