# Memory Index

- [Runtime environment](feedback_environment_runtime.md) — conda python (not `uv run`), HF_HOME + HF_HUB_OFFLINE=1 (kernels pre-cached), DEVICE_BATCH_SIZE=64, ~355-390 s per run.
- [Task measurements](task_autoresearch_measurements.md) — champion 1.094037 at 719 steps; step lever saturated; GQA-1 and wd=0 both DISCARD; empirical seed spread 0.0041.
