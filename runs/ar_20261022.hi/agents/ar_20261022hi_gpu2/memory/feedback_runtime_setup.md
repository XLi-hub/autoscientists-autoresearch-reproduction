---
name: runtime_setup
description: How to launch autoresearch train.py directly with the preinstalled env
type: feedback
---

Use the preinstalled interpreter (uv's shared cache lock can stall):
`CUDA_VISIBLE_DEVICES=1 HF_HOME=/root/autodl-tmp/ar_20261022.hi/.cache/huggingface  TORCH_HOME=/root/autodl-tmp/ar_20261022.hi/.cache/torch  /root/autodl-tmp/envs/ar/bin/python3 train.py`

- HF_HOME must point at the focus-root cache: the `kernels-community/flash-attn3` kernel is
  cached there (NOT in /root/.cache/huggingface).
- Dataset/tokenizer live in /root/.cache/autoresearch (963 MB data + tokenizer); no download needed.
- Expect ~300 s training + ~50-60 s model init/eval = ~370 s wall; the first run in a session
  can take ~490 s (kernel/JIT warmup).
- Copy train.py + prepare.py + pyproject.toml + uv.lock from champion/ before editing.
