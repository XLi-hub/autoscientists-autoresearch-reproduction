---
name: hardware-and-env
description: 32GB OOM fix, cached flash-attn3 location, python invocation
type: feedback
---

# Hardware / environment facts (verified 2026-10-24)

1. **Pristine train.py OOMs on 32GB.** DEVICE_BATCH_SIZE=128 (seq 2048, vocab 8192, fp32 logits
   128*2048*8192 = 8.6GB) exhausts 31.4GB. Set DEVICE_BATCH_SIZE=64; keep TOTAL_BATCH_SIZE at
   2**19 -> grad_accum 4 (effective batch unchanged). Peak VRAM then ~22.8GB.
2. **No internet.** flash-attn3 must come from the prebuilt cache. Use
   `HF_HOME=/root/autodl-tmp/cache/huggingface HF_HUB_OFFLINE=1`. The build there is
   `torch29-cxx11-cu128-x86_64-linux` and matches torch 2.9.1+cu128. The heartbeat's suggested
   `$FOCUS_ROOT/.cache/huggingface` is EMPTY and will attempt a network fetch and fail.
3. **Use the active env python directly** (`/root/autodl-tmp/envs/ar/bin/python`), not `uv run`,
   which may try to sync/download. `sys.executable` in the run harness is correct.
4. **Set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True** explicitly. train.py sets
   PYTORCH_ALLOC_CONF (unused alias) instead of PYTORCH_CUDA_ALLOC_CONF.
5. Data cache: ~/.cache/autoresearch (963MB, 10 shards). Tokenizer also cached there.
