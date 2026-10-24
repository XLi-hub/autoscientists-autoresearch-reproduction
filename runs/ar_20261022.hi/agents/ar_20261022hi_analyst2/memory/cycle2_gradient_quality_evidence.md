---
name: cycle2-gradient-quality-evidence
description: Cycle-2 result classification, step-vs-noise evidence, and queue state for analyst2
type: finding
---

# Cycle 2 (2026-10-22)

Champion moved: baseline_shared 1.195701 -> exp_batch_2e18 1.170054 (TOTAL_BATCH_SIZE 2**19 -> 2**18;
DEVICE_BATCH_SIZE 64; grad_accum 4 -> 2; 193 -> 373 steps; 830 ms/step; 315.6k tok/s;
22,805 MB peak; real MFU ~73%).

Results classified for H-gradient-quality:
- exp_warmup_0p1 +0.027761 DISCARD -> REFUTES (confounded with 30 s budget cost).
- exp_muon_mom_ramp60 +0.004053 DISCARD -> REFUTES (1.35x the 0.003 band, single seed;
  axis stays open, far/opposite-only).
- exp_batch_2e18 KEEP and exp_warmdown_025 DISCARD are ORTHOGONAL (throughput team).
Counters: age_rotations=1, supported_keeps=0, refuted_discards=2.

Load-bearing inference: halving the token batch doubled optimizer steps AND doubled
per-update gradient noise, and val_bpb still improved by 0.0256. Step count dominates
gradient-noise effects at this scale. A gradient-quality probe needs a large effect to win.

Filed: exp_adam_beta2_bracket (beta2 0.99/0.90) and exp_embedding_lr_bracket (1.2/0.3),
both queued with discussion_pending=true. No empirical noise floor yet (no seed pairs).

Open question carried forward: does beta2=0.99 KEEP? If both beta2 probes are flat, the
"gradient noise" lens is weak and the team is one rotation closer to falsification.
