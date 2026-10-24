# ar_20261024 — final report (stagnation stop)

Generated: 2026-10-24T08:57:14.432196+00:00

## Exit condition
0 KEEPs in the last 10 completed experiments -> task-profile stagnation_response.
The result is robust to counting: excluding the calibration run the window is still 0 KEEPs,
and the only KEEP-labelled entry in range (exp_gq_matrix_lr_lo) was refuted by its seed-43 confirmation.

## Champion
exp_tput_batch_2e17 1.088286 ar_20261024_gpu4 2026-10-24T07:39:12.261672+00:00 (TOTAL_BATCH_SIZE 2**18->2**17, grad_accum 2->1, +96.3% steps; NOTE AR=48 from exp_cap_ar48_w384 NOT stacked)
champion/train.py sha1 e102f683c465c99d36ff4779d3d84404831960b7
val_bpb 1.088286 (seed baseline 1.192708 -> -8.8%)

## Run statistics
- experiments logged: 24 (+1 calibration)
- KEEPs: 6
- champion line: baseline 1.192708 -> exp_tput_batch_2e18 1.169258 -> exp_tput_mlp_exp_3 1.158107
  -> exp_tput_compile_autotune 1.147892 -> exp_tput_mlp_exp_2 1.132007 -> exp_tput_batch_2e17 1.088286
- calibrated noise: sigma ~0.0023-0.0025, 2-sigma gate ~0.0047-0.0050 (n=7..8 same-code pairs)

## Channels closed by measurement
- optimizer/EMA horizons: muon momentum, muon beta2, adam beta2, adam beta1 (retired), MATRIX_LR bracket, WEIGHT_DECAY bracket
  (WD is flat because get_weight_decay(p)=WD*(1-p) with WARMDOWN_RATIO=0.5 -> shrink is exactly zero before the run's midpoint,
   while val_bpb is read on end-of-run weights: timing, not magnitude)
- step count / batch size below 2**17 (return per update collapsed 16x once the base passed ~600 steps)
- ASPECT_RATIO / width bracket (384 flat, 640 +0.0089): the historical AR48 KEEP was a step artifact
- HEAD_DIM 64 (+0.0077), head_dim 256 pending; value-embedding density (null on two seeds)
- WINDOW_PATTERN SSLL (inside noise)

## Still open (queued, never run)
- exp_tput_loss_head_precision (chunked fp32 CE; only >3% tok/s lever at bit-identical function)
- exp_cap_head_dim_256 (0-FLOP opposite-direction probe)
- exp_gq_wd_schedule_const (constant WD schedule, proposed by gpu11 to exploit the timing effect)
- exp_cap_depth6_w512 / mlp_exp_5 (low value: capacity-UP now has negative evidence)
