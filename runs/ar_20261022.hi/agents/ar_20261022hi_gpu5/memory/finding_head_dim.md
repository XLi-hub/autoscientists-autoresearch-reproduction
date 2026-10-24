---
name: head-dim-granularity
description: 8x64 heads lose to 4x128 at identical params/FLOPs/steps; the loss is an early-training transient
type: finding
---

exp_head_dim_64 (2026-10-22, team capacity): HEAD_DIM 128->64 at DEPTH=8/ASPECT_RATIO=64 halves n_embd/head_dim
but keeps n_embd=512, n_head 4->8, total params and FLOPs/token EXACTLY identical, steps 725 vs 719.
Result: val_bpb 1.100821 vs champion 1.094037 = +0.006784 (2.25 sigma, real regression).

Mechanism: the gap is almost entirely an early-training transient. vs the ve_all run at the same width:
step 100 +0.3225, step 200 +0.0541, step 400 +0.0173, step 700 +0.0062. Narrower heads converge slower;
in a 300 s fixed-step budget that transient cannot be repaid even if the asymptote were equal.

Do not re-probe head_dim=64. The informative opposite arm is HEAD_DIM 128->256 (n_head 2), queued as
exp_head_dim_256. Also: head_dim is the ONLY structural axis here that is simultaneously param-, FLOP- and
step-neutral, which is why this result is interpretable while depth/width probes are not.
