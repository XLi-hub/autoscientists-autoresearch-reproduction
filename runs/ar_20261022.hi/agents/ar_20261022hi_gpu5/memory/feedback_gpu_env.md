---
name: gpu-env-hf-cache
description: train.py needs HF_HOME + HF_HUB_OFFLINE or the flash-attn3 kernel fetch fails
type: feedback
---

# GPU environment requirements (verified 2026-10-22)

Running `train.py` with the preinstalled `/root/autodl-tmp/envs/ar/bin/python3` still imports
`kernels.get_kernel("kernels-community/flash-attn3")` at module load. The kernel snapshot is
cached ONLY under the shared HF home:

```
HF_HOME=/root/autodl-tmp/ar_20261022.hi/.cache/huggingface
HF_HUB_OFFLINE=1
TORCH_HOME=/root/autodl-tmp/ar_20261022.hi/.cache/torch
```

Without HF_HOME the hub client tries the network and dies with
`httpx.ConnectError: [Errno 99] Cannot assign requested address` ->
`LocalEntryNotFoundError`, before any training starts. The failure is immediate
(import time) and costs a launch, not GPU minutes. Data/tokenizer live in
`~/.cache/autoresearch/` and are already present.
