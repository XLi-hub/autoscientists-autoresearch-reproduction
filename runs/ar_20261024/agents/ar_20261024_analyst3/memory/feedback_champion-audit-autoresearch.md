---
name: champion-audit-autoresearch
description: Champion code facts for ar_20261024 - vocab 8192, 50.33M params, depth/width coupling, VE cost, baseline OOM risk
type: feedback
---

# Champion audit facts (cycle 1)

- **Vocab is 8192, not 32768.** `GPTConfig.vocab_size=32768` is always overridden by `tokenizer.get_vocab_size()` in `build_model_config()`. `prepare.py` builds 8192 tokens (8188 merges + 4 specials). Champion model is **50.33M params**, decomposition: 25.17M transformer blocks + 16.78M value-embeds + 4.19M wte + 4.19M lm_head + 16 scalars.
- **Depth and width are coupled.** `model_dim = DEPTH * ASPECT_RATIO` rounded up to a multiple of HEAD_DIM=128. DEPTH=12 alone (AR=64) is 135.3M params (+169%). To test depth alone, co-adjust AR: (6,85), (8,64), (12,42) all give width 512.
- **Value embeddings are a huge capacity dial.** `has_ve(i,n)` is parity-based; n_layer=8 -> 4 VE layers, 12 -> 6, 6 -> 3. Each VE is 8192*512 = 4.19M params = 8.3% of the champion model, MORE than the 3.15M cost of one transformer block. Depth scaling is VE-dominated.
- **Baseline memory risk.** At DEVICE_BATCH_SIZE=128 the final logits are [128,2048,8192] = 4.29GB bf16 / 8.59GB float; MLP intermediates ~1.07GB/layer at batch 128; total ~28-30GB on 32GB. Memory-safe baseline: device batch 64, TOTAL_BATCH_SIZE=2**19 (grad_accum=4).
- **MFU reporting is wrong for this GPU.** `H100_BF16_PEAK_FLOPS=989.5e12` is hardcoded; on RTX 4080S (~1/10 the dense bf16 peak) printed `mfu_percent` is understated ~10x. Use tokens/sec and step count for compute-budget audits.
- Cold start at cycle 1: 0 results, `champion.md` status `awaiting_baseline`.

# Champion code facts (cycle 2, re-audited at exp_tput_batch_2e17)

- **The ASPECT_RATIO axis is quantized.** `build_model_config` does
  `model_dim = ceil(depth * ASPECT_RATIO / HEAD_DIM) * HEAD_DIM` (HEAD_DIM=128). At DEPTH 8 the
  reachable widths are {128, 256, 384, 512, 640, 768}; **AR 49-64 all build width 512**, i.e. the
  entire midpoint between the winning AR48 and champion AR64 is unreachable. AR56 = 8*56 = 448 ->
  512 = the champion, a literal no-op. Fine brackets on AR at fixed depth are impossible; only far
  probes (AR32 -> 256, AR96 -> 768) are real. Same trap applies to depth: (6,85)->512, (12,42)->512
  were chosen deliberately for exactly this reason.
- **Param budget at MLP_EXPANSION=2, AR64 (width 512), DEPTH 8, vocab 8192 = 41.94M:**
  wte 4.19M + lm_head 4.19M + 4 VE tables 16.78M (40.0% of the model!) + 8 blocks 16.78M + 16 scalars.
  AdamW scope = 25.17M = **60.0%**; Muon scope = 16.78M = 40.0%. The "54%" in older notes was the
  MLP-3x (46.14M) champion. The old 50.33M figure was the MLP-4x champion.
- **Only four constants in train.py are step-count-coupled** (everything else runs off
  `progress = total_training_time/TIME_BUDGET`, which is wall-clock): `get_muon_momentum`'s
  `min(step/300,1)` (line 528-530), `ADAM_BETAS` beta2 (445), the muon group `beta2=0.95` (261), and
  the x0 group betas (0.96,0.95) (255).
  At the 956-step champion: muon ramp saturates at 31.4% of the run (arguably correct — that is what
  the 300 constant was authored for); Adam beta2 horizon = 20 steps = **2.09% of the run** (it was
  10.2% at 196 steps, 4.6% at 433). The batch ladder halved the relative memory of every optimizer EMA
  twice, so Adam-family betas are now the freshest step-count story, not the muon ramp.
- **`momentum=0.95` at line 261 is dead** — `group["momentum"] = muon_momentum` overwrites it every
  step before `_step_muon` reads it.
- **`step > 10` free-step gate lags `progress` by 11 steps.** Any progress-based schedule saturates
  ~6 steps earlier than the equivalent step-based one on a 956-step run. Matters for null-detection.
