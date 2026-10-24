---
name: environment-runtime
description: How to actually run train.py on this box (conda env + HF offline cache + 32GB batch limit)
type: feedback
---

# Runtime environment for ar_20261022.hi (2x RTX 4080S 32GB)

## Use the pre-provisioned conda env, not a fresh `uv run` venv
`/root/autodl-tmp/envs/ar/bin/python3` has torch 2.9.1+cu128, kernels, tiktoken,
rustbpe, pyarrow, pandas, matplotlib. Verified working across 5 runs on 2026-10-22.

```bash
cd {FOCUS_ROOT}/agents/{AGENT}/workspace/repo
CUDA_VISIBLE_DEVICES=0 \
HF_HOME=$FOCUS_ROOT/.cache/huggingface \
HF_HUB_OFFLINE=1 \
/root/autodl-tmp/envs/ar/bin/python3 train.py
```

Do NOT use `uv run python train.py`: it builds a fresh `.venv` and pulls ~2-4 GB of
torch/nvidia wheels (>10 min on this box). The shared uv cache also deadlocks when
two agents start concurrently.

## flash-attn3 kernel — cached, run offline
`kernels.get_kernel("kernels-community/flash-attn3")` is already cached at
`$FOCUS_ROOT/.cache/huggingface/hub/models--kernels-community--flash-attn3`.
With `HF_HOME` set to that directory and `HF_HUB_OFFLINE=1`, training starts with no
network access. This is the verified path (cycle 3, two consecutive runs, cold starts
~55-60 s). Only if the cache is ever missing would you fall back to
`HF_HUB_ENDPOINT=https://hf-mirror.com` (mirror returns 429 and retries at ~35 s).

## Memory ceiling
`DEVICE_BATCH_SIZE = 128` (upstream default) OOMs: the 50.3M-param model emits a
128x2048x8192 logits tensor and train.py keeps fp32 + tanh copies, ~31 GB peak.
Use **64** (peak 22.65 GB at width 512; 19.85 GB with n_kv_head=1).
`TOTAL_BATCH_SIZE` is independent of this.

## Data
`~/.cache/autoresearch/` already has shards 0-9 + the val shard + the tokenizer.
No `prepare.py` run needed.

## Wall clock per experiment
~355-390 s total: ~55-90 s startup (warm inductor cache), 300.3 s training, ~55 s eval.
`torch.compile` adds ~90 s only on a cold inductor cache. The inner subprocess timeout
should be >=560 s; the outer Bash tool call 600 s.
val_bpb comes from the final summary block (`val_bpb: <float>`), parsed by regex.
`mfu_percent` uses the H100 peak-FLOPS constant; multiply by ~9.5 for the real value.
