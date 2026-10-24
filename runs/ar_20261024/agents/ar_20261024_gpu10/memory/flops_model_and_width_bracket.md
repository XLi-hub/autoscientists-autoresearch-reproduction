---
name: flops_model_and_width_bracket
description: Analytic params/FLOPs model of train.py is exact for matrix (width) axes; the width bracket is closed at the 956-step base
type: finding
---

# Analytic model of the nanoGPT train.py (validated)

With vocab=8192, DEPTH=8, HEAD_DIM=128, window SSSL (6 short + 2 long layers), n_kv_head=n_head:

    model_dim = ceil(DEPTH*ASPECT_RATIO / 128) * 128      # 8*64=512, 8*80=640
    transformer_matrices = DEPTH * (4 + 2*MLP_EXPANSION) * w^2
    embeddings = 6 * V * w        # wte + lm_head + 4 VE tables (kv_dim == w when n_kv_head == n_head)
    params = matrices + embeddings + 2*DEPTH
    FLOPs/tok = 6*(params - exclude) + 12*(n_head*head_dim)*(6*(seq//2) + 2*seq)
    exclude = V*w + 4*V*w + 2*DEPTH

Validated to +0.01% against both the champion (AR64: 41.94M params, 1.8874e8 FLOPs/tok) and
exp_cap_ar80_w640 (AR80: 57.72M measured vs 57.67M predicted, FLOPs exact, steps 682 vs 675 predicted,
tok/s 292.6K vs 290.2K predicted).

**Key asymmetry:** this FLOPs ratio is an excellent *step* predictor for matrix-dominated axes
(width, MLP) — AR80 error +1.0%. It FAILED for attention-layout changes (exp_cap_window_ssll predicted
-5.6% steps, measured -0.9%) because attention is memory/kernel-bound at seq 2048 on this GPU.
Always predict steps from the 6N matrix term, never from the attention term.

# Width bracket is CLOSED at the 956-step base (AR64/MLP2/TOTAL 2**17 champion)

| width | exp | steps | val_bpb | delta vs 512 |
|---|---|---|---|---|
| 384 | exp_cap_ar48_b2e17 | 1348 | 1.088598 | +0.000312 (0.12 sigma) |
| 512 | champion | 956 | 1.088286 | 0 |
| 640 | exp_cap_ar80_w640 | 682 | 1.097234 | +0.008948 (3.36 sigma) |

Both directions worse. The early AR64->48 KEEP (-0.037 at a 433-step base) was a *step-count artifact*,
not a capacity effect: the same lever at 956 steps is worth +0.0003. Do not refile fine AR points
(72/88/etc.) — with DEPTH=8, AR is quantized to width in {128,256,384,512,640,768}.

Peak VRAM at width 640 / dbs 64 = 24,669 MB (75% of 32.8 GB) — fits, no fallback needed.
Cost of new head shapes in max-autotune: total wall 563.9s vs 381.8s champion (+83s compile/eval).

# Capacity scoreboard at the 956-step base (closed this cycle)

| arm | params | steps | delta vs 1.088286 | verdict |
|---|---|---|---|---|
| exp_cap_ar80_w640 | +37.5% (57.7M) | -28.7% (682) | +0.008948 (3.36 sigma) | capacity UP costs |
| exp_cap_ve_density_2 (2 seeds) | -20.0% (33.6M) | -0.9% (947/948) | +0.002852 (1.07 sigma) | flat / null |
| exp_cap_ar48_b2e17 | -32.5% (28.3M) | +41.0% (1348) | +0.000312 (0.12 sigma) | flat |
| exp_cap_head_dim_64 | ~0 | -0.8% (948) | +0.007723 (2.70 sigma) | structure hurts |

**Removing parameters is free; adding them is not.** A 33.6M model matches the 41.94M champion
within noise, but capacity-UP (width 640) costs ~+0.009 bpb. The residual error at this compute is
not capacity-limited. Do not spend slots on capacity scale-ups (depth12 carries the same failing bet
at a larger step cost). Remaining capacity value is head geometry (head_dim 256 untested) only.

VE-2 penalty-free parameter removal is also a practical lever: if a future change needs memory/
optimizer-state headroom it can be paid for with VE density at zero val_bpb cost (it is NOT a step
lever though — VE params are excluded from estimate_flops, FLOPs stay identical).

Noise ledger after this cycle: n=8 pairs, sigma 0.002335 (2-sigma 0.00467). Our same-GPU cross-seed
pair on VE-2 was |delta| 0.002252. Note other agents logged a 0.000413 pair and a 0.004396 pair —
per-pair seed variance is broad; never promote on a single seed inside ~2 sigma.
