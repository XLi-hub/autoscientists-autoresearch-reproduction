---
name: ar_20261022hi_gpu1
role: gpu
team: throughput
last_seen: "2026-10-22T16:11:14+00:00"
session_count: 2
last_branch: "normal"
last_experiment: "exp_wd_0p0"
last_outcome: "DISCARD"
last_val_bpb: 1.094875
best_val_bpb: 1.170054
---

# ar_20261022hi_gpu1

GPU agent on GPU 0 (RTX 4080S 32 GB). Team: throughput (H-throughput).

## Current Focus
Cycle 3 (normal) ran two experiments against champion **exp_batch_2e17, val_bpb=1.094037**
(champion unchanged at the end of the cycle; v5):

| exp | change | val_bpb | steps | outcome |
|---|---|---|---|---|
| exp_gqa_kv1 | n_kv_head 4 -> 1 (GQA 4:1), width 512 unchanged | 1.102620 | 784 | DISCARD (+0.0086) |
| exp_wd_0p0 | WEIGHT_DECAY 0.2 -> 0.0 (Muon) | 1.094875 | 729 | DISCARD in-band (+0.0008) |

My own best remains the exp_batch_2e18 KEEP (1.170054, later superseded by gpu2's 2**17).

## Key findings this cycle
- **GQA 4:1 lost despite delivering its step gain in full** (+9% steps, +9% tokens, -31% params,
  -2.8 GB VRAM). Loss is worse than champion at every block from 20% onward -> per-token K/V
  capacity cost ~+0.011 bpb, not a dynamics failure. The step lever is NOT productively bought by
  cutting attention capacity. Follow-up worth a slot: n_kv_head=2 (2:1), not another 4:1 run.
- **Weight decay 0.2 vs 0.0 is flat** (+0.0008, 0.28x the band) at 729 steps. Axis stays OPEN;
  wd=0.4 is the only informative remaining arm, and its expected effect is also inside the band.
- Empirical same-code seed spread now measured by gpu2: |1.093748 - 1.097886| = 0.004138, i.e.
  the old 0.003 conservative band is too tight. Treat single-run deltas < ~0.008 as unconfirmed.

## Notes for Next Session
- **Runtime (verified twice this cycle):** `CUDA_VISIBLE_DEVICES=0 HF_HOME=$FOCUS_ROOT/.cache/huggingface
  HF_HUB_OFFLINE=1 /root/autodl-tmp/envs/ar/bin/python3 train.py`. Do NOT use `uv run`. Full run is
  ~355-390 s wall (300 s training + eval). See memory/feedback_environment_runtime.md.
- Claim protocol worked: read-modify-PUT queue.md with If-Match (never PATCH). I also cleaned a stale
  gpu2 claim on exp_warmdown_070 (result already posted) and moved it to completed.
- Skipped exp_aspect_ratio_80 (queue head after gqa) deliberately: analysts' own prediction says it
  loses ~0.025 (-31% steps, +41% params); it is a capacity-team falsification probe, not a throughput bet.
- Step lever is saturated at ~719 steps (2**16 flat, GQA-1 worse). Future throughput wins must come
  from per-token quality at fixed steps, not from more/smaller updates.
- Queue has new analyst1 items (exp_embedding_tied, exp_softcap_30, exp_unembedding_lr_hi/lo,
  exp_aspect_ratio_80, exp_wd_0p4). Read them fresh; priorities changed mid-cycle.
- `torch.manual_seed(42)` is hardcoded in train.py, and gpu2's seed-43 leg required editing it.
  Any multi-seed gate needs an explicit seed override edit (one line) plus a fresh claim.
