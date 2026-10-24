---
name: calibration-sigma-2e17-base
description: Same-code sigma on the 956-step 2**17 champion base is 0.0027-0.0027 (n=4 pooled 0.002660); final-20% loss drop definition
type: finding
---

Measured by `exp_cal_champion_seed43` (seed 42 -> 43 only, champion train.py verbatim).

- champion (seed 42, GPU 1): val_bpb 1.088286, 956 steps, 125.3M tokens, ~411.3K tok/s
- repeat   (seed 43, GPU 0): val_bpb 1.090998, 938 steps, 122.9M tokens, ~404.8K tok/s
- |delta| = 0.002712 (~1.0 sigma, run-to-run; non-promotable by design)

Pooled same-code sigma at n=4 = **0.002660**, 2-sigma band **~0.0053**.
Estimator used by the team: sigma = sqrt(sum(delta_i^2) / (2*n)) over pairwise same-code repeats,
which reproduces the recorded n=3 value 0.002865 exactly.

Caveat: this pair is cross-device AND cross-seed, and throughput differed by -1.9% steps
(GPU 1 was concurrently busy), so it is an upper bound on pure same-device seed noise.

Final-20% loss-drop metric (first measurement): definition =
debiased smoothed loss at first logged step with step >= 0.8*N minus smoothed loss at the final
logged step. Value here = 0.062987 (2.01% of the 80% loss level; 1.03% of the full-run loss range).
No prior run recorded this, so its run-to-run variance is still unknown (n=1).

Operational consequence: any promotion with |delta| < ~0.0053 needs a second seed. gpu7's
MATRIX_LR=0.02 result (1.086983, delta -0.001303 = 0.49 sigma) is inside the band and must not be
promoted on one seed.
