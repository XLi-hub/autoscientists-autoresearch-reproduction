---
name: runtime-environment
description: How to launch autoresearch training on this box (uv hangs, HF kernel cache, 32GB OOM floor)
type: feedback
---

- `uv run python train.py` HANGS on this machine (uv attempts dependency resolution; the run cache is empty).
  The Python/uv env is already active: run plain `python train.py` from the repo directory.
- The flash-attn3 kernel is pre-cached at `/root/autodl-tmp/cache/huggingface`. Set
  `HF_HOME=/root/autodl-tmp/cache/huggingface` and `HF_HUB_OFFLINE=1`; without HF_HOME, `kernels.get_kernel`
  tries to re-download and stalls.
- Data (`~/.cache/autoresearch` -> `/root/autodl-tmp/cache/autoresearch`) and tokenizer are already present.
- Pristine upstream `DEVICE_BATCH_SIZE=128` OOMs on the 32GB RTX 4080S (31.35GB in use; 8.6GB fp32 logits
  tensor is the dominant consumer). `DEVICE_BATCH_SIZE=64` is the hardware floor; peak VRAM 20-23GB.
- Per-training wall time: ~370s (300s budget + ~70s startup/compile); max-autotune compile adds ~150s.
