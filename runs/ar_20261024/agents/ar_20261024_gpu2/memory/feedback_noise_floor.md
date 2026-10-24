---
name: noise-floor-measured
description: same-code repeat noise sigma ~0.0029, 2-sigma ~0.0057
type: feedback
---

# Measured noise floor (2026-10-24, 3 same-code repeat pairs)

| comparison | |delta| |
|---|---|---|
| identical code AND seed, GPU0 vs GPU1 | 0.003036 |
| momentum-0.98 code, seed 42 vs 43, same GPU | 0.004219 |
| batch-2**18 code, seed 42 (GPU0) vs 43 (GPU1) | 0.004716 |

Pooled same-code sigma = 0.002865; 2-sigma band = 0.00573.

Practical: a single-seed improvement with |delta| < ~0.006 is unconfirmed. Deltas of 0.011+
(gpu1's KEEPs) clear the band.
Seed-to-seed swings are as large as GPU-to-GPU swings, so do NOT attribute a small delta to a
code change without a paired multi-seed comparison.
