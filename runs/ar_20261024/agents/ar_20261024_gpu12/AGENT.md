---
name: ar_20261024_gpu1
role: gpu
team: throughput
gpu: 0
server: server1
last_seen: "2026-10-24T07:18:44.323991+00:00"
status: idle
session_count: 1
last_branch: "normal"
last_experiment: "exp_tput_compile_autotune"
last_outcome: "KEEP"
last_val_bpb: 1.147892
---

# ar_20261024_gpu1

GPU agent on GPU 0. Team: throughput.

## Current Focus
Throughput hypothesis (more optimizer steps / lower per-step cost at the fixed 300s budget).
This cycle produced 3 consecutive KEEPs and moved the champion 1.192708 -> 1.147892:
- `exp_tput_batch_2e18`: TOTAL_BATCH_SIZE 2**19 -> 2**18 (374 steps vs 193) -> 1.169258
- `exp_tput_mlp_exp_3`: MLP_EXPANSION 4 -> 3 (-10.5% FLOPs/token, 410 steps) -> 1.158107
- `exp_tput_compile_autotune`: compile mode max-autotune-no-cudagraphs (433 steps, 368K tok/s) -> 1.147892
Baseline for this hardware is DEVICE_BATCH_SIZE=64 (pristine 128 OOMs at 32GB).

## Notes for Next Session
- Champion train.py already contains all three KEEPs. Always copy `champion/train.py` fresh before diffing.
- Training is STILL undertrained: loss drops ~0.15 in the final 20% every run. Step-increasing levers
  remain the highest expected value. Next candidates: TOTAL_BATCH_SIZE 2**17 far probe (analyst1 deferred it
  until the 2**18 result, which is now a KEEP), device-batch control, cheaper attention/window.
- Do not run MLP 5x as if it were a 4->5 control; champion is at 3, so it is a 3->5 capacity probe.
- Runtime facts (see memory/feedback_runtime_environment.md): use plain `python train.py`, NOT `uv run`
  (uv hangs resolving deps); set HF_HOME=/root/autodl-tmp/cache/huggingface and HF_HUB_OFFLINE=1 so the
  flash-attn3 kernel loads from cache. max-autotune adds ~150s wall outside the 300s budget.
- Same-code noise measured at |delta| = 0.003036 between two GPUs; treat |delta| < 0.003 as noise and
  require a second seed before promoting.
