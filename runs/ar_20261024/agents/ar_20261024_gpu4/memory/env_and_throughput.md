---
name: autoresearch-env-and-throughput
description: Verified launch recipe + hardware facts for the autoresearch nanoGPT task, and the measured throughput levers
type: reference
---

# Autoresearch (ar_20261024) — verified environment facts and throughput levers

## Launch recipe that works (GPU 1)
```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate /root/autodl-tmp/envs/ar
# python is /root/autodl-tmp/envs/ar/bin/python  (torch 2.9.1+cu128)
CUDA_VISIBLE_DEVICES=1 \
HF_HOME=/root/autodl-tmp/cache/huggingface HF_HUB_OFFLINE=1 \
TORCH_HOME=/root/autodl-tmp/ar_20261024/.cache/torch \
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
python train.py
```
- The flash-attn3 kernel cache lives at `/root/autodl-tmp/cache/huggingface`. The
  `$FOCUS_ROOT/.cache/huggingface` path is EMPTY — using it plus HF_HUB_OFFLINE=1 fails.
- `uv run` is not needed; the conda env `/root/autodl-tmp/envs/ar` already has torch+kernels.
- Training data is at `~/.cache/autoresearch/{data,tokenizer}` (prepare.py reads it).
- Wall time: first run with a new graph ~520s (compile/autotune ~140-150s inside step 0, which is
  OUTSIDE the 300s counted budget because of the `if step > 10` gate). Re-running a graph whose
  inductor/autotune cache already matches costs only ~35s -> ~380s total.
- `run_in_background` + the harness notification is the way to run a 320-560s training; a
  foreground Bash call hits the 120s default timeout.

## Hardware facts
- 2x RTX 4080 SUPER, 32760 MiB each. Two agents run concurrently (one per GPU) — expect the other
  GPU to be busy.
- `DEVICE_BATCH_SIZE=128` OOMs at seq 2048 (the lm_head logits path dominates: 131072 x 8192 bf16
  logits upcast to fp32). 64 is the max that fits at model_dim 512; peak VRAM 18-23GB.
- `mfu_percent` in the log is normalised to H100 peak (989.5 TFLOP/s) — meaningless here. Real
  utilisation on the 4080S is ~3x the reported number (~8% -> ~25-32% of peak bf16).
- Model in the champion lineage: DEPTH 8, ASPECT_RATIO 64 -> model_dim 512, n_head 4, vocab 8192.

## Measured throughput lever ranking (val_bpb, minimize; sigma ~0.0029)
| change | steps | val_bpb | delta |
|---|---|---|---|
| baseline (2**19, MLP 4x, DBS 64) | 193 | 1.192708 | — |
| TOTAL_BATCH_SIZE 2**19->2**18 | 374 | 1.169258 | -0.0234 |
| MLP_EXPANSION 4x->3x | 410 | 1.158107 | -0.0112 |
| compile max-autotune-no-cudagraphs | 433 | 1.147892 | -0.0102 |
| MLP_EXPANSION 3x->2x | 487 | 1.132007 | -0.0159 |
| ASPECT_RATIO 64->48 (gpu3) | 632 | 1.094760 | -0.0372 |
| TOTAL_BATCH_SIZE 2**18->2**17 | 956 | 1.088286 | -0.0437 |

Two independent levers, both = "reduce FLOPs/token or add optimizer steps": per-step cost and
optimizer-step count. Both keep paying. Per-token throughput (tok/s) is insensitive to grad_accum
(411-418K), and per-step fixed overhead is only ~1-3ms of a 318ms step, so halving the micro-batch
nearly halves step wall time.

## Measurement discipline learned
- The champion file is a single global best AND the code lineage. When two teams improve orthogonal
  axes in the same window, promoting the better metric silently drops the other team's code change.
  Always note un-stacked improvements in `champion.md` / `champion/SOURCE`.
- `champion.md` frontmatter uses `metric_name` + `metric_value`; `direction: minimize`.
