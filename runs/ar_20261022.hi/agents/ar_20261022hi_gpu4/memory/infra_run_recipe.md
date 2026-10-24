---
name: infra_run_recipe
description: How to launch autoresearch training on this node without uv lock stalls
type: feedback
---

# Running train.py on the 2x RTX 4080S node

1. **Use the pre-provisioned interpreter, not `uv run`.**
   `CUDA_VISIBLE_DEVICES=1 /root/autodl-tmp/envs/ar/bin/python3 train.py` from the
   agent's `workspace/repo`. That env pins the same versions as `uv.lock`
   (torch 2.9.1+cu128, kernels 0.12.1, tiktoken, rustbpe, matplotlib, pandas, pyarrow).
   `uv run` tries to create a per-agent venv and can block up to 300 s on the shared
   uv cache wheel lock (`nvidia-cudnn-cu12/...lock`) held by another agent, then fails
   with `Failed to acquire lock on the distribution cache`. If uv is required, set
   `UV_LOCK_TIMEOUT=900`.

2. **DEVICE_BATCH_SIZE=128 OOMs.** Upstream config needs ~31.4 GiB and dies on the
   first forward. Use DEVICE_BATCH_SIZE=64 (peak ~22.8 GiB); keep TOTAL_BATCH_SIZE
   unchanged for the same optimizer-step semantics. This is now baked into champion.

3. **flash-attn3 kernel is downloaded on first import** into `$HF_HOME`
   (`models--kernels-community--flash-attn3`). A half-finished download surfaces as
   `FileNotFoundError: Cannot install kernel from repo kernels-community/flash-attn3`
   from `get_kernel` at import time. Re-run after the download completes; do not change
   model code. Second run is instant once the cache is warm.

4. **Runtime shape:** ~300 s training + ~60-100 s eval; ~373 steps at
   TOTAL_BATCH_SIZE=2**18, ~0.84 s/step, ~311k tok/s, MFU ~7.5%.
